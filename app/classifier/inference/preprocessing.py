# Owner: HAWRAA
import torch
from PIL import Image
from torchvision import transforms


def get_transform() -> transforms.Compose:
    return transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


def preprocess_image(image_path: str) -> torch.Tensor:
    img = Image.open(image_path)
    return get_transform()(img).unsqueeze(0)  # shape: [1, 3, 224, 224]
