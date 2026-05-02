import nibabel as nib

abs_path = "C:\\Users\\sarah\Documents\\5 èMME ANNéE\\PFE\\Tools and software\\SAMT Back\\backend\\media\\IXI020-Guys-0700-T2_IWUAdft.nii"
img = nib.load(abs_path)
print(img)
print("hello there")
