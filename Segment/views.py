import base64
from io import BytesIO
import json
import os
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from PIL import Image
from django.views.decorators.http import require_GET
import torch
from transformers import SamModel, SamProcessor
import numpy as np
from .models import Patients, MRI_Masks, Structures
from Auth.models import Doctors
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
import time
import numpy as np
from django.utils import timezone


print("🧠 Loading SAM model... (this may take a moment)")
_start = time.perf_counter()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"   Using device: {DEVICE}")

try:
    SAM_MODEL = SamModel.from_pretrained("facebook/sam-vit-huge").to(DEVICE)
    
    SAM_PROCESSOR = SamProcessor.from_pretrained("facebook/sam-vit-huge")
    SAM_MODEL.eval()  # Set to evaluation mode
    print(f"✅ SAM model loaded in {time.perf_counter() - _start:.2f}s")
except Exception as e:
    print(f"❌ Failed to load SAM model: {e}")
    SAM_MODEL = None
    SAM_PROCESSOR = None

#===================================
#       GET ALL THE STRUCTURES
#===================================
@api_view(['GET'])
def Get_Structures(request): 
      # fetch the structures from the database 
      try :
            structures = Structures.objects.all()
            if structures : 
                  data = [
                        {
                              "id" : s.structure_id,
                              "title" : s.structure_name, 
                              } 
                        for s in structures
                        ]
                  return Response({
                        "message" : "Structures Recieved with sucsess!", 
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
# =====================================================
#   Retreive the structures created by the Annotator
# =====================================================           
@api_view(['POST'])
def myStructures(request) : 
      patient_id = request.data.get("patient_id")
      doc_id = request.doc_id
      modality = request.data.get('modality')

      if not patient_id or not modality : 
            return Response({
            "message" : "Required Feilds missing!"
            }, status = status.HTTP_400_BAD_REQUEST)
      try : 
            # check if the doc and patient exist 
            patient = Patients.objects.get(patient_id = patient_id, modality = modality)
            print("from my structures")
            print(patient)
            doc = Doctors.objects.get(id = doc_id)

            # check if they re assigned
            mask = MRI_Masks.objects.filter(doctor = doc, patient = patient)
            if mask.exists() : 
                  mystructures = [
                        {
                              "structure_id": m.structure.structure_id,
                              "structure_title": m.structure.structure_name,
                              "structure_color": m.structure_color,
                              "coordinates": m.coordinates or []
                              }
                              for m in mask
                              if m.structure is not None 
                  ]
                  return Response({
                  "message" : "Annotators structures received with success !",
                  "mystructures" : mystructures
                  }, status = status.HTTP_200_OK)
            else : 
                  return Response({
                        "message" : "This Annotator is not assigned to this patient", 
                        },status = status.HTTP_200_OK)

      except Patients.DoesNotExist : 
            return Response({
                  "message" : "Patient does not exist!"
                  }, status = status.HTTP_200_OK)
      except Doctors.DoesNotExist : 
            return Response({
                  "message" : "Annotator does not exist!"
                  }, status = status.HTTP_200_OK)
      except MRI_Masks.DoesNotExist: 
            return Response({
                  "message" : "This doctor is not assigned to the Patient!"
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
             return Response({
                  "message" : f"uh i guess smthn went wrong : {e}", 
                  }, status = status.HTTP_200_OK)

# ======================= 
#   Add New Structure
# =======================
@api_view(['POST'])
def AddStructure(request) : 
      patient_id = request.data.get("patient_id")
      doc_id = request.doc_id
      structure = request.data.get("structure")
      modality = request.data.get("modality")
      print(modality)
      
      if not structure or not patient_id or not modality : 
            return Response({
                  "message" : "Required Fields missing !"
                  }, status = status.HTTP_200_OK)

      try : 
            # check if the doc and patient exist 
            patient = Patients.objects.get(patient_id = patient_id, modality = modality)
            print("from add structure")
            print(patient)
            doc = Doctors.objects.get(id = doc_id)

            # check if the doctor is assigned to the patient
            masks = MRI_Masks.objects.filter(doctor = doc, patient = patient)

            # check if the structure exists 
            structu = Structures.objects.get(structure_id = structure['id'])

            # check if the structure already exists :
            if masks.exists() and structu: 
                  # if there is not structure created i.e. the structure is null for the doctor - patient pair
                  # this case is possible because the model for patient-doctors is not independent of Masks model
                  null_mask = masks.filter(structure__isnull=True).first()
                  print("from adding structure, the null mask is :")
                  print(null_mask)
                  if null_mask : 
                        null_mask.structure = structu
                        null_mask.structure_color = structure["color"]
                        null_mask.coordinates = structure["coordinates"]
                        null_mask.save()
                        return Response({
                              "message": "structure saved with success !"
                              }, status = status.HTTP_200_OK)    
                  else : 
                        # check if the structure already exists :
                        mask = MRI_Masks.objects.get(doctor = doc, patient = patient, structure = structu)
                        return Response({
                                    "message": "it Already exists!"
                                    }, status = status.HTTP_400_BAD_REQUEST)
            else : 
                  return Response({
                        "message" : "Either the Patient is not assigned to this Doctor, or the Structure does not exist!"
                        }, status = status.HTTP_400_BAD_REQUEST)
      except MRI_Masks.DoesNotExist :
            MRI_Masks.objects.get_or_create(doctor = doc, patient = patient, structure = structu, structure_color = structure["color"], coordinates = structure["coordinates"])     
            return Response({
                              "message": "structure saved with success !"
                              }, status = status.HTTP_200_OK) 
      except Patients.DoesNotExist :     
            return Response({
                              "message": "Patient does not exist !"
                              }, status = status.HTTP_200_OK) 
      except Doctors.DoesNotExist :     
            return Response({
                              "message": "Doctor does not exist !"
                              }, status = status.HTTP_200_OK) 
      except Structures.DoesNotExist :     
            return Response({
                              "message": "Structure does not exist !"
                              }, status = status.HTTP_200_OK) 
      except Exception as e : 
             return Response({
                  "message" : f"Exception : {e}", 
                  }, status = status.HTTP_200_OK)

# =============================================
# Fetching the masks of each mri to be rated 
# =============================================
# def receive_selected_structures(request): 
#       patient_id = request.data.get("patient_id")

#       # check the patient exists 
#       pt = Patients.objects.get(patient_id = patient_id).DoesNotExist
#       if pt : 
#             return Response({
#                   "message" : "Invalid patient ID"
#                   }, status = status.HTTP_200_OK)
      
#       # if the patient exists, then we fetch all of its mri masks 
#       else : 
#             masks = MRI_Masks.objects.get(patient = patient_id)

# =====================================================
#  Fetch Patients meta data The Annotator assigned to
# =====================================================
@api_view(['GET'])
def MRI_List_For_Segment(request):
      doc_id = request.doc_id 
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
                              m = p.patient.modality
                              tup = (pid,m)
                              # if tup not in seen:
                              #       seen.add(tup)
                              dt = p.last_modified
                              formatted = f"{dt.year}-{dt.month}-{dt.day} {dt.strftime('%H:%M')}"
                              data.append({
                                          "patient_id": pid,
                                          "sex": p.patient.gender,
                                          "age": str(p.patient.age),
                                          "last_modified":  formatted,
                                          "mri_path": p.patient.mri.url,
                                          "modality" : p.patient.modality
                                    })
                        # print(data)
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


# =============================================
#          Add Coordinates Function
# =============================================
@api_view(["POST"])
def Add_Coordinates(request): 
      coordinates = request.data.get("coordinates")
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      modality = request.data.get("modality")
      doc_id = request.doc_id

      if not coordinates or not patient_id or not structure_id : 
            return Response({
                  "message" : "Missing required fields!"
                  }, status = status.HTTP_400_BAD_REQUEST)     
      
      try:
            doc = Doctors.objects.get(id = doc_id) 
            structure = Structures.objects.get(structure_id = structure_id) 
            patient = Patients.objects.get(patient_id = patient_id, modality = modality)
            mask = MRI_Masks.objects.get(patient = patient, structure = structure, doctor = doc)
            # add the new coordinates 
            coords = {
                  "x" : coordinates["x"], 
                  "y" : coordinates["y"], 
                  "z" : coordinates["z"], 
                  "hasSegmentation" : False,
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
      

# =============================================
#              Update the coordinates
# =============================================
@api_view(["POST"])
def Update_Coordinates(request): 
      """
      The following function is called when the user adds a new tuple of coordinates.
      The list of the coordinates is overwritten by the one received from then frontend.
      then stored to the masks model.
      """
      coordinates = request.data.get("coordinates")
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      doc_id = request.doc_id
      modality = request.data.get('modality')

      if not coordinates or not patient_id or not structure_id : 
            return Response({
                  "message" : "Missing required fields!"
                  }, status = status.HTTP_400_BAD_REQUEST)

      try:
            doc = Doctors.objects.get(id = doc_id) 
            structure = Structures.objects.get(structure_id = structure_id) 
            patient = Patients.objects.get(patient_id = patient_id, modality = modality)
            mask = MRI_Masks.objects.get(patient = patient, structure = structure, doctor = doc)
            
            # add the new coordinates 
            coords = [{
                  "x" : coor["x"], 
                  "y" : coor["y"], 
                  "z" : coor["z"], 
                  "hasSegmentation" : coor['hasSegmentation'],
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
def Has_segmentation(request) :
      coordinates = request.data.get("coordinates")
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      doc_id = request.doc_id
      modality = request.data.get('modality')

      if not coordinates or not patient_id or not structure_id : 
            return Response({
                  "message" : "Missing required fields!"
                  }, status = status.HTTP_400_BAD_REQUEST)
      try : 
            # check f everyone exist
            doc = Doctors.objects.get(id = doc_id) 
            structure = Structures.objects.get(structure_id = structure_id) 
            patient = Patients.objects.get(patient_id = patient_id, modality = modality)
            mask = MRI_Masks.objects.get(patient = patient, structure = structure, doctor = doc)

            coords = mask.coordinates
            for i, coord in enumerate(coords):
                  if (coord["x"], coord["y"], coord["z"]) == (coordinates["x"], coordinates["y"], coordinates["z"]):
                        coords[i]["hasSegmentation"] = True
                        break
            mask.coordinates = coords 
            mask.save()
            return Response({
            "message"  : "Coordinates updated with success"
            }, status = status.HTTP_200_OK)

      except ObjectDoesNotExist as e : 
            return Response({
                  "message" : f"Exception : {e}"
                  }, status = status.HTTP_400_BAD_REQUEST)
      except Exception as e : 
            return Response({
                  "message" : f"Exception : {e}"
                  }, status = status.HTTP_400_BAD_REQUEST)
# =============================================
#              Load the mask 
# =============================================
@api_view(['POST'])
def Load_mask(request) :
      patient_id = request.data.get("patient_id")
      structure_id = request.data.get("structure_id")
      modality = request.data.get('modality')
      doc_id = request.doc_id
      
      try : 
            # load the mask 
            patient = Patients.objects.get(patient_id = patient_id, modality = modality)
            structure = Structures.objects.get(structure_id = structure_id)
            doc = Doctors.objects.get(id = doc_id)
            mask = MRI_Masks.objects.get(patient = patient, doctor = doc, structure = structure )
            with open(mask.mask_path.path, "rb") as f:
                  mask_bytes = f.read()
            # return FileResponse(open(mask.mask_path.path, "rb"), content_type="application/octet-stream")

            dims = [dim for dim in mask.dims]
            mask_base64 = base64.b64encode(mask_bytes).decode("utf-8")  
            data = {
                  "mask_id" : mask.mask_id, 
                  "patient_id" : patient_id, 
                  "structure_id" : structure_id, 
                  "mask_path" : mask.mask_path.url, 
                  "mask_data" : mask_base64,
                  "mask_dims" : dims ,
                  "mask_color" : mask.structure_color,
                  "modality" : mask.patient.modality
                  }
            return Response({
                  "message" : "Mask loaded successfully!",
                  "mask" : data
                  }, status = status.HTTP_200_OK)
      except Patients.MultipleObjectsReturned: 
            return Response({
                  "message" : "multiple rows were found patients",
                  "mask" : ""
                  }, status = status.HTTP_200_OK)
      except Doctors.MultipleObjectsReturned: 
            return Response({
                  "message" : "multiple rows were found doctors",
                  "mask" : ""
                  }, status = status.HTTP_200_OK)
      except Structures.MultipleObjectsReturned: 
            return Response({
                  "message" : "multiple rows were found structures",
                  "mask" : ""
                  }, status = status.HTTP_200_OK)
      except MRI_Masks.MultipleObjectsReturned: 
            duplicates =  MRI_Masks.objects.filter(patient = patient, doctor = doc, structure = structure )
            print("Multiple rows found:")
            for p in duplicates:
                  print(f"Patient ID: {p.mask_id}, structure: {p.structure.structure_name}")
            return Response({
                  "message" : "multiple rows were found",
                  "mask" : ""
                  }, status = status.HTTP_200_OK)
      except ObjectDoesNotExist : 
            return Response({
                  "message" : "Mask does not exist!",
                  "mask" : ""
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"some exception : {e}",
                  "mask" : ""
                  }, status = status.HTTP_200_OK)

# =============================================
#              Create the mask 
# =============================================
@api_view(['POST'])
def save_mask(request) : 
      patient_id = request.data.get("patient_id")
      structure_id = int(request.data.get('structure_id'))
      mask = request.FILES.get('mask')
      dims_raw = request.data.get('dims')
      dims = json.loads(dims_raw) if dims_raw else None
      doc_id = request.doc_id
      modality = request.data.get('modality')
      if not mask:
        return Response(
            {"message": "No mask file provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not structure_id:
        return Response(
            {"message": "No structure_id provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not patient_id:
        return Response(
            {"message": "No patient_id provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not doc_id:
        return Response(
            {"message": "No doc_id provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not dims_raw:
        return Response(
            {"message": "No dims provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not modality: 
            return Response(
            {"message": "No modality provided."},
            status=status.HTTP_400_BAD_REQUEST
        )

            
      try :
            # check that the patient exists
            p = Patients.objects.get(patient_id = patient_id, modality = modality)

            # check if the doc exists
            doc = Doctors.objects.get(id = doc_id)

            # check that the struct exists
            struct = Structures.objects.get(structure_id = structure_id)

            # check that the structure was created for the mask 
            # of the mri of this patient
            mri_mask = MRI_Masks.objects.get(doctor = doc, patient = p, structure = struct)
            if mri_mask.mask_path : 
                  return Response({
                        "message": "the mask already exists, sending back the mask id",
                        "mask_id" : mri_mask.mask_id
                        },status = status.HTTP_200_OK)

            else: 
                  # create the nii file
                  # raw_data = np.frombuffer(mask.read(), dtype=np.uint8).reshape((dims[0], dims[1], dims[2]))
                  # img = nib.Nifti1Image(raw_data, np.eye(4))

                  # # temporary save path
                  # temp_path = f"media/Masks/mask-{structure_id}-{patient_id}.nii.gz"
                  # nib.save(img, temp_path)

                  # # now store in Django model
                  # with open(temp_path, "rb") as f:
                  #       django_file = File(f)
                  #       mri_mask.mask_path.save(os.path.basename(temp_path), django_file, save=True)

                  # # remove temp file
                  # os.remove(temp_path)
                  #  rename the file first, to include the doc id

                  mask_content = mask.read()
                  renamed_mask = ContentFile(mask_content)
                  new_name = f"mask-{doc_id}-{patient_id}-{modality}-{structure_id}.raw"
                  renamed_mask.name = new_name

                  mri_mask.dims = dims
                  mri_mask.mask_path = renamed_mask 
                  mri_mask.last_modified = timezone.now()
                  mri_mask.save()


                  return Response({
                  "message" : "mask created with success !", 
                  "mask_id" : mri_mask.mask_id
                  }, status = status.HTTP_200_OK)

      except Patients.DoesNotExist: 
                  return Response({
                  "message" : "Patient id invalid!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
      except Doctors.DoesNotExist  :
                  return Response({
                  "message" : "Patient is yet to be assinged!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
      except Structures.DoesNotExist : 
                  return Response({
                  "message" : "Struct sent does not exist i guess!", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
      except MRI_Masks.DoesNotExist:
                  return Response({
                  "message" : "The structure is yet to be created or the patient is not assigned to the Doc", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
      except Exception as e : 
            return Response({
                  "message" : f"some exception :{e}", 
                  "mask_id" : ""
                  }, status = status.HTTP_200_OK)
      
# =============================================
#              Updating the mask 
# =============================================
@api_view(['POST'])
def Update_mask(request) : 
      patient_id = request.data.get("patient_id")
      structure_id = int(request.data.get('structure_id'))
      mask = request.FILES.get('file')
      modality = request.data.get('modality')
      dims_raw = request.data.get('dims')
      dims = json.loads(dims_raw) if isinstance(dims_raw, str) else dims_raw
      dims = [int(d) for d in dims]
      doc_id = request.doc_id

      # check the request data availability
      # print(modality)
      if not mask:
        return Response(
            {"message": "No mask file provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not structure_id:
        return Response(
            {"message": "No structure_id provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not patient_id:
        return Response(
            {"message": "No patient_id provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not doc_id:
        return Response(
            {"message": "No doc_id provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not dims:
        return Response(
            {"message": "No dims provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      elif not modality:
            return Response(
            {"message": "No modality provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
      try :
            # check that the patient exists
            p = Patients.objects.get(patient_id = patient_id, modality = modality)

            # check if the doc is assiged to this patient 
            doc = Doctors.objects.get(id = doc_id)

            # check if the structure exists 
            struct = Structures.objects.get(structure_id = structure_id)

            # check if the mri row exracted does not have the same structure to create a new one.
            # Otherwise, return the corresponding mask_id
            mri_mask = MRI_Masks.objects.select_for_update().get(doctor = doc, patient = p, structure = struct)
            # ======================
            #   Saving mask as nii
            # ======================
            # now lets update the mask 
            # first we create the nii format file 
            # print("from updaitng the mask, the dims",(dims[0], dims[1], dims[2]))
            # affine =  [[-8.91676366e-01,  3.93992029e-02 ,-2.28674680e-01 , 9.98072052e+01],
            #            [ 4.39754836e-02 , 8.96562934e-01, -8.42658207e-02 ,-1.14962555e+02],
            #             [-1.00848764e-01 , 4.25933301e-02 , 1.98509109e+00 ,-5.91814995e+01],
            #             [ 0.00000000e+00 , 0.00000000e+00 , 0.00000000e+00 , 1.00000000e+00]]

            # raw_data = np.frombuffer(mask.read(), dtype=np.uint8).reshape((dims[0], dims[1], dims[2]))
            # img = nib.Nifti1Image(raw_data, affine)

            # # temporary save path
            # temp_path = f"media/Masks/mask-{structure_id}-{patient_id}.nii.gz"
            # nib.save(img, temp_path)
            # ======================
            #         END
            # ======================

            if not mri_mask.mask_path : 
                  mask.name = f"mask-{doc_id}-{patient_id}-{structure_id}-{modality}.raw"
            else : 
                  mask.name = os.path.basename(mri_mask.mask_path.name)

            # if the mask exists, we delete the previous version
            old_path = mri_mask.mask_path.path
            # Delete the old file first to avoid duplicate errors
            if os.path.exists(old_path):
                  # print("Deleting the older version of the mask ...")
                  os.remove(old_path)
                  
            mri_mask.mask_path.save(mask.name, mask, save=True)
            mri_mask.last_modified = timezone.now()
            mri_mask.save()
                  
            return Response({
                  "message": f"Mask {mri_mask.mask_path.url} updated with success!"
                  },status = status.HTTP_200_OK)
            
      except Patients.DoesNotExist : 
                  return Response({
                  "message" : "Patient id invalid!", 
                  }, status = status.HTTP_400_BAD_REQUEST)
      except Doctors.DoesNotExist:
                  return Response({
                  "message" : "Patient is yet to be assinged!", 
                  }, status = status.HTTP_400_BAD_REQUEST)
      except Structures.DoesNotExist: 
                  return Response({
                  "message" : "Struct sent does not exist i guess!", 
                  }, status = status.HTTP_400_BAD_REQUEST)
      except MRI_Masks.DoesNotExist:
                  return Response({
                  "message" : "The mask for this structure is not created, or the  patient does not correspond to this doctor", 
                  }, status = status.HTTP_400_BAD_REQUEST)
      except Exception as e : 
            return Response({
                  "message" : f"some exception :{e}", 
                  }, status = status.HTTP_400_BAD_REQUEST)
       
# =============================
#        Segmenting MRI 
# =============================
@api_view(['POST'])
def SAM(request):
    start_total = time.perf_counter()  # measure total time

    # ------------------------------
    # 1️⃣  Get request data
    # ------------------------------
    t0 = time.perf_counter()
    file_data = request.data.get("file")
    coords = request.data.get("coords")
    t1 = time.perf_counter()
    print(f"[STEP 1] Read request data: {t1 - t0:.3f}s")

    if not file_data or not coords:
        return Response({"message": "Required Fields Missing!"}, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------
    # 2️⃣  Parse coordinates
    # ------------------------------
    try:
        t0 = time.perf_counter()
        x = coords.get('x')
        y = coords.get('y')
        z = coords.get('z')
        coordinates = [[[int(x), int(y)]]]
        t1 = time.perf_counter()
        print(f"[STEP 2] Parse coordinates: {t1 - t0:.3f}s")
    except Exception as e:
        return Response({
            "message": "coordinates of wrong format",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------
    # 3️⃣  Decode image
    # ------------------------------
    try:
        t0 = time.perf_counter()
        if file_data.startswith('data:image'):
            file_data = file_data.split(',')[1]
        image_bytes = base64.b64decode(file_data)
        image = Image.open(BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        t1 = time.perf_counter()
        print(f"[STEP 3] Decode image: {t1 - t0:.3f}s")
    except Exception as e:
        return Response({
            "message": "Something went wrong when processing file",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------
    # 4️⃣  Inference (MODEL ALREADY LOADED!)
    # ------------------------------
    try:
        t0 = time.perf_counter()
        inputs = SAM_PROCESSOR(image, input_points=coordinates, return_tensors="pt").to(DEVICE)
        
        with torch.no_grad():
            outputs = SAM_MODEL(**inputs)
        
        t1 = time.perf_counter()
        print(f"[STEP 4] SAM inference: {t1 - t0:.3f}s")
    except Exception as e:
        return Response({
            "message": "Error during SAM inference",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------
    # 5️⃣  Preprocess mask
    # ------------------------------
    t0 = time.perf_counter()
    masks = SAM_PROCESSOR.image_processor.post_process_masks(
        outputs.pred_masks.cpu(),
        inputs["original_sizes"].cpu(),
        inputs["reshaped_input_sizes"].cpu()
    )
    mask = masks[0][0][0].numpy()
    binary_mask = (mask > 0.5).astype(np.uint8) * 255
    t1 = time.perf_counter()
    print(f"[STEP 5] Postprocess masks: {t1 - t0:.3f}s")

    # ------------------------------
    # 6️⃣  Encode mask to base64
    # ------------------------------
    t0 = time.perf_counter()
    mask_image = Image.fromarray(binary_mask, mode='L')
    buffered = BytesIO()
    mask_image.save(buffered, format="PNG")
    mask_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    t1 = time.perf_counter()
    print(f"[STEP 6] Encode mask: {t1 - t0:.3f}s")

    # ------------------------------
    # ✅ Total time
    # ------------------------------
    total_time = time.perf_counter() - start_total
    print(f"=== TOTAL SAM FUNCTION TIME: {total_time:.3f}s ===")
    
    return Response({
        "mask": f"data:image/png;base64,{mask_base64}",
        "mask_shape": list(mask.shape),
        "coords_used": coords
    }, status=status.HTTP_200_OK)




