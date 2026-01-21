import torch
import torchreid
from torchvision import transforms
import cv2
import numpy as np

class ReIDModel:
    def __init__(self):
        self.device = torch.device("cpu")

        self.model = torchreid.models.build_model(
            name="osnet_x1_0",
            num_classes=1000,
            pretrained=True
        )
        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def extract_embedding(self, img):
        if img is None or img.size == 0:
            return None

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            feat = self.model(img)

        return feat.cpu().numpy()[0]
