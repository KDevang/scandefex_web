import torch
from torchvision import models, transforms
from PIL import Image
import base64
from io import BytesIO
from django.shortcuts import render

# Load ResNet18 with 2 output classes
model = models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(model.fc.in_features, 2)

try:
    model.load_state_dict(torch.load('model/defecscan_resnet18_binary.pth', map_location=torch.device('cpu')))
    model.eval()
except Exception as e:
    print(f"🔥 Error loading model: {e}")
    model = None  # Prevent crash if model load fails

# Define preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

class_labels = ['No Defect', 'Defect']

def index(request):
    result = None
    if request.method == 'POST' and model:
        image_data = request.POST.get('image_data')
        if image_data:
            try:
                image_data = image_data.split(',')[1]
                image = Image.open(BytesIO(base64.b64decode(image_data))).convert('RGB')
                input_tensor = transform(image).unsqueeze(0)

                with torch.no_grad():
                    output = model(input_tensor)
                    probs = torch.nn.functional.softmax(output[0], dim=0)
                    pred_class = torch.argmax(probs).item()
                    confidence = probs[pred_class].item() * 100

                    result = f"Detected: {class_labels[pred_class]} (Confidence: {confidence:.2f}%)"
            except Exception as e:
                result = f"❌ Error during prediction: {e}"
    elif not model:
        result = "❌ Model failed to load."

    return render(request, 'index.html', {'result': result})
