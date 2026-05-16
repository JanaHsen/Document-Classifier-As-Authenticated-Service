#!/usr/bin/env python
"""Benchmark cached endpoints to verify latency budgets.

- Uncached p95 < 200ms
- Cached p95 < 50ms

Requires:
- Redis running on settings.REDIS_URL (default redis://localhost:6379/0)
- Database seeded with sample data (run scripts/seed_data.py and seed_policies.py)
"""

import asyncio
import sys
import time
from pathlib import Path
from statistics import quantiles

# Load environment variables from .env before any other imports
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=dotenv_path)
    print("Loaded environment from .env")
else:
    print("Warning: .env file not found; using system environment.")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.main import app, lifespan
from fastapi_cache import FastAPICache

BASE_URL = "http://test"
N_UNCACHED = 10
N_CACHED = 50

async def main():
    print("Initializing benchmark...")

    # Enter app lifespan to start up cache and other resources
    async with lifespan(app):
        print("App lifespan started.")
        # Ensure cache is initialized
        if FastAPICache._backend is None:
            print("ERROR: FastAPICache not initialized.")
            sys.exit(1)
        print("Cache backend initialized.")

        # Clear any existing cache
        await FastAPICache.clear()

        async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
            # Register a benchmark user with known credentials
            test_email = "benchmark@example.com"
            test_password = "Benchmark123!"
            try:
                resp = await client.post(
                    "/auth/register",
                    json={"email": test_email, "password": test_password},
                )
                if resp.status_code == 200:
                    print(f"Registered benchmark user: {test_email}")
                else:
                    print(f"Register responded {resp.status_code}: {resp.text}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    print("User already exists, proceeding")
                else:
                    raise

            # Login to get token
            resp = await client.post(
                "/auth/jwt/login",
                data={"username": test_email, "password": test_password},
            )
            resp.raise_for_status()
            token = resp.json()["access_token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
            print("Obtained JWT token")

            # Endpoints to test: (name, path, method)
            endpoints = [
                ("GET /users/me", "/users/me", "GET"),
                ("GET /batches", "/batches", "GET"),
                ("GET /batches/{id}", "/batches/1", "GET"),
                ("GET /predictions/recent", "/predictions/recent", "GET"),
            ]

            results = {}

            for name, path, method in endpoints:
                print(f"\n--- Benchmarking {name} ---")
                kwargs = {"headers": auth_headers}

                # Uncached measurements (clear cache before each)
                uncached_times = []
                for i in range(N_UNCACHED):
                    await FastAPICache.clear()
                    start = time.perf_counter()
                    resp = await client.request(method, path, **kwargs)
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    resp.raise_for_status()
                    uncached_times.append(elapsed_ms)
                up95 = quantiles(uncached_times, n=100)[94]
                print(f"  Uncached p95: {up95:.2f} ms")

                # Cached measurements (no clear)
                cached_times = []
                for i in range(N_CACHED):
                    start = time.perf_counter()
                    resp = await client.request(method, path, **kwargs)
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    resp.raise_for_status()
                    cached_times.append(elapsed_ms)
                cp95 = quantiles(cached_times, n=100)[94]
                print(f"  Cached p95: {cp95:.2f} ms")

                results[name] = {
                    "uncached_ms": uncached_times,
                    "cached_ms": cached_times,
                    "uncached_p95": up95,
                    "cached_p95": cp95,
                }

            # Summary
            print("\n=== BENCHMARK SUMMARY ===")
            all_ok = True
            for name, data in results.items():
                u_p95 = data["uncached_p95"]
                c_p95 = data["cached_p95"]
                print(f"{name}: uncached p95={u_p95:.2f}ms (target <200ms), cached p95={c_p95:.2f}ms")
                if u_p95 >= 200 or c_p95 >= 50:
                    all_ok = False

            if all_ok:
                print("\nAll endpoints meet latency budgets.")
            else:
                print("\nSome endpoints exceed latency budgets.")

            print("About to write results file...")
            output_path = Path(__file__).parent / "benchmark_results.txt"
            with open(output_path, "w") as f:
                for name, data in results.items():
                    f.write(f"{name}: uncached_p95={data['uncached_p95']:.2f}ms, cached_p95={data['cached_p95']:.2f}ms\n")
                f.flush()
            print(f"Results saved to {output_path}")
            return results

if __name__ == "__main__":
    asyncio.run(main())
