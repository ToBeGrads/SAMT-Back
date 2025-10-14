import base64
from io import BytesIO
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from PIL import Image


import torch
from transformers import SamModel, SamProcessor
import numpy as np
# Create your views here.
@api_view(['POST'])
def SAM(request) : 
    file_data = request.data["file"]
    coords = request.data["coords"]

    # read the coordinates 
    try :
        x = coords.get('x')
        y = coords.get('y')
        z = coords.get('z')

        coordinates = [[[int(x),int(y)]]]
    except Exception as e: 
        print("problem with the coordinates",str(e))
        return Response({
            "status" : False, 
            "message" : "coordinates of wrong format", 
            "error" : str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    # prep the image to be segmented 
    try : 
        if file_data.startswith('data:image'):
                file_data = file_data.split(',')[1]
        image_bytes = base64.b64decode(file_data)
        image = Image.open(BytesIO(image_bytes))
        if image.mode != 'RGB':
                image = image.convert('RGB')
    except Exception as e: 
          print("problem with the image",str(e))
          return Response({
            "status" : False, 
            "message" : "Something went wrong when processing file",
            "error" : str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # laoding the segment anything model 
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SamModel.from_pretrained("facebook/sam-vit-huge").to(device)
    processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

    inputs = processor(image, input_points=coordinates, return_tensors="pt").to(device)
    print("generating the mask")
    with torch.no_grad():
            outputs = model(**inputs)
    
    masks = processor.image_processor.post_process_masks(
            outputs.pred_masks.cpu(),
            inputs["original_sizes"].cpu(),
            inputs["reshaped_input_sizes"].cpu()
        )
        
        # Get the first mask
    mask = masks[0][0][0].numpy()
    binary_mask = (mask > 0.5).astype(np.uint8) * 255

    mask_image = Image.fromarray(binary_mask, mode='L')

    buffered = BytesIO()
    mask_image.save(buffered, format="PNG")
    mask_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return Response({
            "success": True,
            "mask": f"data:image/png;base64,{mask_base64}",
            "mask_shape": list(mask.shape),
            "coords_used": coords
        })

