import base64
from io import BytesIO
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from PIL import Image
import csv
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import torch
from transformers import SamModel, SamProcessor
import numpy as np
from .models import Patients, MRI_Masks, Structures
from .serializers import MRIMASKSSerializer
from Auth.models import Doctors
from django.core.exceptions import ObjectDoesNotExist


#===========================#
#       SRUCTURES VIEWS
#===========================#

#============ Fetching the structures ============#
@api_view(['GET'])
def Get_Structures(request): 
      # fetch the structures from the database 
      try :
            structures = Structures.objects.all()
            if structures : 
                  print(structures)
                  data = [
                        {
                              "id" : s.structure_id,
                              "title" : s.structure_name, 
                        } 
                        for s in structures
                        ]
                  return Response({
                        "message" : "Structures sent with sucsess", 
                        "structures" : data
                        }, status = status.HTTP_200_OK)
            else : 
                  return Response({
                        "message" : "The structures table is yet to be populated", 
                        "structures" : ""
                        },status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"An error occured{e}", 
                  "structures" : ""
                  }, status = status.HTTP_400_BAD_REQUEST)



#============ Fetching the meta data of the patients the doc was assigned to ============#
@api_view(['GET'])
def MRI_List_For_Segment(request):
      doc_id = request.doc_id 
      print(doc_id)
      print(Doctors.objects.get(id = doc_id))
      print(Doctors.objects.filter(id=doc_id))
      # check if the doc exists 
      doc = Doctors.objects.filter(id = doc_id)
      if not doc.exists() : 
            return Response({
                  "message" : "no record with such doc id"
                  },status = status.HTTP_200_OK)
      else : 
            # check if this doc is asseigned yet
            doc_mri = MRI_Masks.objects.filter(doctor = doc_id)
            if doc_mri.exists() : 
                  # return the mris 
                  mris = MRI_Masks.objects.filter(doctor=doc_id).select_related('patient')
                  if mris.exists():
                        seen = set()
                        data = []
                        for p in mris:
                              pid = p.patient.patient_id
                              if pid not in seen:
                                    seen.add(pid)
                                    data.append({
                                          "patient_id": pid,
                                          "sex": p.patient.gender,
                                          "age": str(p.patient.age),
                                          "status": p.patient.status,
                                          "mri_path": p.patient.mri.url
                                    })

                        return Response({
                              "message" : "fetching mris with success", 
                              "mris" : data
                              
                              }, status = status.HTTP_200_OK)
                  else : 
                        return Response({
                              "message" : "Doctor is not yet assigned to patient !", 
                              "mris" : ""
                              }, status = status.HTTP_200_OK)
            else : 
                return Response({
                              "message" : "Doctor is not yet assigned to patient !", 
                              "mris" : ""
                              }, status = status.HTTP_200_OK)

                  
#========================================#                
#     Structures related views
#========================================#                
@api_view(['POST'])
def myStructures(request) : 
      patient_id = request.data.get("patient_id")
      doc_id = request.doc_id
      try : 
            # check if the doc and patient exist 
            patient = Patients.objects.get(patient_id = patient_id)
            doc = Doctors.objects.get(id = doc_id)

            # check if they re assigned
            mask = MRI_Masks.objects.filter(doctor = doc, patient = patient)
            mystructures = []
            # print("check",mask.exists())
            if mask.exists() : 
                  for m in mask : 
                        structs = { 
                              "structure_id" : m.structure.structure_id, 
                              "structure_title" : m.structure.structure_name, 
                              "structure_color" : m.structure_color,
                              "coordinates" : m.coordinates
                              }
                        mystructures.append(structs)
                  print(mystructures)
                  return Response({
                  "message" : "Yay you got your structures dumbass!",
                  "mystructures" : mystructures
                  }, status = status.HTTP_200_OK)
            else : 
                  return Response({
                        "message" : "this doc is not assigned to this patient", 
                        "mystructures" : mystructures
                        },status = status.HTTP_200_OK)

      except ObjectDoesNotExist as e : 
            return Response({
                  "message" : "Either doc or patient does not exist, or this doctor is not assigned to the patient"
                  ,"mystructures" : mystructures
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
             return Response({
                  "message" : f"uh i guess smthn went wrong : {e}", 
                  "mystructures" : mystructures
                  }, status = status.HTTP_200_OK)

#============ Create a new mask and assing structure to it ============#
# here is the case when we add structure through + button in the sidebar, it creates the structure but without the mask
@api_view(['POST'])
def AddStructure(request) : 
      patient_id = request.data.get("patient_id")
      doc_id = request.doc_id
      structure = request.data.get("structure")
      try : 
            # check if the doc and patient exist 
            patient = Patients.objects.get(patient_id = patient_id)
            doc = Doctors.objects.get(id = doc_id)

            # check if they re assigned
            mask = MRI_Masks.objects.filter(doctor = doc, patient = patient)

            # check if the structure exists 
            structu = Structures.objects.get(structure_id = structure['id'], structure_name = structure["title"])

            # check if the structure already exists :
            if mask.exists() and structu: 
                  # check if the structure already exists :
                  mask = MRI_Masks.objects.filter(doctor = doc, patient = patient, structure = structu)
                  if mask.exists(): 
                        return Response({
                              "message": "it Already exists!"
                              }, status = status.HTTP_400_BAD_REQUEST)
                  else : 
                        mask.structure_color = structure["color"]
                        mask.coordinates = structure["coordinates"]
                        mask.save()
                        
                        return Response({
                              "message": "structure saved with success !"
                              }, status = status.HTTP_200_OK)
            else : 
                  return Response({
                        "message" : "either the patient is not assigned or the structure does not exist"
                        }, status = status.HTTP_200_OK)
      except ObjectDoesNotExist as e : 
            return Response({
                  "message" : "Either doc or patient does not exist, or this doctor is not assigned to the patient, maybe the structure does not exist idk, uk"
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
             return Response({
                  "message" : f"uh i guess smthn went wrong : {e}", 
                  }, status = status.HTTP_200_OK)

#============ Create a new mask and assing structure to it ============#
def Select_Structure(request) : 
      structure_id = request.data.get("structure_id")
      patient_id = request.data.get("patient_id")
      doc_id = request.data.get("doc_id") # change later to be extracted from the jwt
      mask = request.data.get("mask")
      try :
            # check if the patient exists 
            patient = Patients.objects.get(patient_id=patient_id).DoesNotExist
            if patient : 
                  return Response({
                        "message" : "Patient id not valid",
                        "mask_id" : "", 
                        "mask_path" : ""
                        }, status = status.HTTP_200_OK)
            else : 
                # create row in the MRI masks table 
                mri_mask_serializer = MRIMASKSSerializer(
                structure = structure_id,
                patient = patient_id, 
                doctor = doc_id, 
                mask_path = mask 
                )
                if mri_mask_serializer.is_valid(): 
                      return Response({
                            "message" : "mask stored successfully", 
                            "mask_path" : mri_mask_serializer.mask_path.url, 
                            "mask_id" : mri_mask_serializer.mask_id
                            }, status = status.HTTP_200_OK)
                else : 
                      return Response({
                            "message" : "Validation failed of mask data", 
                            "mask_path" : "", 
                            "mask_id" : ""
                            }, status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"An error occured :{e}", 
                  "mask_path" : "", 
                  "mask_id" : ""
                  }, status = status.HTTP_400_BAD_REQUEST)



#============ Fetching the structures of each doctor ============#
@api_view(['GET'])
def fetch_doc_patient_mri(request): 
      patient_id = request.data.get("patient_id")
      doc_id = request.data.get('doc_id')  # change later to be extracted from the jwt

      patient_exists = False
      doc_exists = False
      # check the patient exists 
      pt = Patients.objects.get(patient_id = patient_id).DoesNotExist
      if not pt : 
        patient_exists = True

      # check if the doctor exists
      doc = Doctors.objects.get(id = doc_id)
      if not doc.DoesNotExist : 
            doc_exists = True
      
      if doc_exists and patient_exists : 
            # now check if that doctor has that patient mri assigned to them 
            mask_mri = MRI_Masks.objects.get(doctor = doc_id, patient = patient_id)
            if mask_mri.DoesNotExist : 
                  return Response({
                        "message" : "UUUUUHM this patient is not urs sir"
                        },status = status.HTTP_200_OK)
            else : 
                  # new both doctor and patient exist, and this patient mri is indeed assgined to this doc 
                  # return the mask
                  return Response({
                        "hello world !"
                        }, status = status.HTTP_200_OK)



#============ Fetching the masks of each mri to be rated ============#
def receive_selected_structures(request): 
      patient_id = request.data.get("patient_id")

      # check the patient exists 
      pt = Patients.objects.get(patient_id = patient_id).DoesNotExist
      if pt : 
            return Response({
                  "message" : "Invalid patient ID"
                  }, status = status.HTTP_200_OK)
      
      # if the patient exists, then we fetch all of its mri masks 
      else : 
            masks = MRI_Masks.objects.get(patient = patient_id)

      


            
#============ Fetching the coordinates ============#
@api_view(['POST'])
def Get_Coordinates(request): 
      mask_id = request.data.get("mask_id")
      doc_id = request.data.get("doc_id") # change later to read it through the middleware
      # check if the mask exists 
      try : 
            mask = MRI_Masks.objects.get(mask_id = mask_id)
            return Response({
                  "message" : "Coordinates retreived with success !", 
                  "coordinates" : mask.coordinates
            },status = status.HTTP_200_OK)
      except ObjectDoesNotExist as e: 
            return Response({
                  "message" : "Invalid mask id !", 

                  },status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f" exception :{e}", 
                  },status = status.HTTP_400_BAD_REQUEST)


#============ Add the coordinates ============#
@api_view(["POST"])
def Add_Coordinates(request): 
      coordinates = request.data.get("coordinates")
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      doc_id = request.doc_id
      print("oh hi there !")
      # return "respond you f*head !"

      try:
            doc = Doctors.objects.get(id = doc_id) 
            structure = Structures.objects.get(structure_id = structure_id) 
            patient = Patients.objects.get(patient_id = patient_id)
            mask = MRI_Masks.objects.get(patient = patient, structure = structure, doctor = doc)
            # add the new coordinates 
            coords = {
                  "x" : coordinates["x"], 
                  "y" : coordinates["y"], 
                  "z" : coordinates["z"], 
                  "orientation": coordinates["orientation"]
                  }
            # check if the coordinates already exist 
            is_duplicate = any(
                  c["x"] == coords["x"] and
                  c["y"] == coords["y"] and
                  c["z"] == coords["z"] and
                  c.get("orientation") == coords["orientation"]
                  for c in mask.coordinates
            )
            print("dup is",is_duplicate)
            if is_duplicate:
                  return Response({
                        "message": "These coordinates already exist for this mask.",
                        "duplicate_coordinate": coords
                  }, status=status.HTTP_200_OK)
            
            # append to the list of coordinates 
            mask.coordinates.append(coords)
            mask.save()

            return Response({
            "message": "Coordinates added successfully",
            "new_coordinate": coords,
            "mask_id": mask.mask_id
        }, status=status.HTTP_200_OK)

            
      except ObjectDoesNotExist : 
            return Response({
                  "message" : "Invalid mask, row does not exist!"
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"exception : {e}"
                  }, status = status.HTTP_400_BAD_REQUEST)

#============ Update the coordinates ============#
@api_view(["POST"])
def Update_Coordinates(request): 
      coordinates = request.data.get("coordinates")
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      doc_id = request.doc_id
      print("oh hi there !")
      # return "respond you f*head !"

      try:
            doc = Doctors.objects.get(id = doc_id) 
            structure = Structures.objects.get(structure_id = structure_id) 
            patient = Patients.objects.get(patient_id = patient_id)

            mask = MRI_Masks.objects.get(patient = patient, structure = structure, doctor = doc)
            
            # add the new coordinates 
            coords = [{
                  "x" : coor["x"], 
                  "y" : coor["y"], 
                  "z" : coor["z"], 
                  "orientation": coor["orientation"]
                  } for coor in coordinates]
            
            # append to the list of coordinates 
            mask.coordinates = []
            mask.coordinates = coords
            mask.save()

            return Response({
            "message": "Coordinates updated successfully",
            "coordinates": mask.coordinates,
            "mask_id": mask.mask_id
        }, status=status.HTTP_200_OK)

            
      except ObjectDoesNotExist : 
            return Response({
                  "message" : "Invalid mask, row does not exist!"
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"exception : {e}"
                  }, status = status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def save_mask(request) : 
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      mask = request.FILES.get('mask')
      structure_color = request.data.get("color")
      print(structure_color)

      print(mask)
      doc_id = request.doc_id
      

      # for exception 
      from_patient = False
      from_doc = False
      from_struct = False
      
      try :
            from_patient = True
            # check that the patient exists
            p = Patients.objects.get(patient_id = patient_id)

            # check if the doc is assiged to this patient 
            from_doc = True
            doc = Doctors.objects.get(id = doc_id)
            mris = MRI_Masks.objects.filter(doctor = doc, patient = p)

            # check if the mri row exracted does not have the same structure 
            # to create a new one otherwise, return the corresponding mask_id
            from_struct = True
            struct = Structures.objects.get(structure_id = structure_id)
            if mris.exists(): 
                  for mri in mris : 
                        if mri.structure == struct : 
                              return Response({
                              "message": "the mask already exists, sending bakc the mask id",
                              "mask_id" : mri.mask_id
                              },status = status.HTTP_200_OK)

                  # create the mask 
                  mask = MRI_Masks.objects.get_or_create(doctor = doc, patient = p, structure = struct, mask_path = mask, structure_color = structure_color)

                  return Response({
                  "message" : "mask created with success !", 
                  "mask_id" : mri.mask_id
                  }, status = status.HTTP_200_OK)
            
            else : 
                  return Response({
                  "message" : "Patient is yet to be assinged!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)

      except ObjectDoesNotExist:
            if from_patient : 
                  return Response({
                  "message" : "Patient id invalid!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
            elif from_doc :
                  return Response({
                  "message" : "Patient is yet to be assinged!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
            elif from_struct: 
                  return Response({
                  "message" : "Struct sent does not exist i guess!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
            else:
                  return Response({
                  "message" : "Invalid doc id!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"some exception :{e}", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
       
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





# @api_view(['POST'])
# def load_patients(request):
#     file_path = 'assets/patients.csv'  

#     try:
#         with open(file_path, newline='', encoding='utf-8') as csvfile:
#             reader = csv.DictReader(csvfile)
#             count = 0
#             for row in reader:
#                 Patients.objects.update_or_create(
#                     patient_id=row['Patient ID'],
#                     defaults={
#                         'gender': row['Sex'],
#                         'date_of_birth': row['birth_date'],
#                     }
#                 )
#                 count += 1

#         return JsonResponse({"message": f"{count} patients imported successfully!"})

#     except FileNotFoundError:
#         return JsonResponse({"error": "patients.csv file not found."}, status=404)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
