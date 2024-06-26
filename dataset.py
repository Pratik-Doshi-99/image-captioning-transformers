import pandas as pd
import Vocabulary as v 
import os
from PIL import Image 
import torch
from torch.utils.data import Dataset, DataLoader
import captionPreprocessing
import urllib.request
import zipfile
import torchvision.transforms as transforms
import numpy as np

np.random.seed(123)


'''
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
                                                DOWNLOAD DATA
'''




# Replace with your ZIP file URL
DATASET = 'https://gitlab.nrp-nautilus.io/pratikdoshi/data_files/-/raw/main/image-captioning-project/flickr8k.zip' #Flick8k
#DATASET = 'https://gitlab.nrp-nautilus.io/pratikdoshi/data_files/-/raw/main/image-captioning-project/flickr8k_m.zip'  #Test dataset
# Specify the directory where the file should be downloaded
DOWNLOAD_DIRECTORY = os.path.join('.','data') # current directory
# the name of the directory inside the zip which has the Images sub directory and captions.txt file
DEST_DIRECTORY = 'flickr8k'

def download_and_unzip(url, download_directory, dest_dir, filename='data.zip'):

    target_dir = os.path.join(download_directory, dest_dir)
    if os.path.isdir(target_dir):
        print(f'Target dir={target_dir} exists. Skipping Download')
        return target_dir


    # Create the download directory if it does not exist
    os.makedirs(download_directory, exist_ok=True)
    
    # Path to save the downloaded ZIP file
    zip_file_path = os.path.join(download_directory, filename)
    
    # Download the ZIP file
    print(f"Downloading ZIP file from {url}...")
    urllib.request.urlretrieve(url, zip_file_path)
    print(f"ZIP file downloaded to {zip_file_path}")
    
    # Unzip the contents
    print(f"Unzipping the contents of {zip_file_path}...")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(download_directory)
        print(f"Contents extracted to {download_directory}")
    
    # Optionally, remove the ZIP file after extraction
    os.remove(zip_file_path)
    print(f"ZIP file removed: {zip_file_path}")

    return target_dir


def get_default_device():
  """Pick GPU if available, else CPU"""
  device = "cuda" if torch.cuda.is_available() else \
         ("mps" if torch.backends.mps.is_available() else "cpu" ) 
  return device




'''
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
                                                Data Split
'''


def data_split(train_val_test=(0.7,0.15,0.15)):
    print(f'Splitting Dataset: Train={train_val_test[0]}, Val={train_val_test[1]}, Test={train_val_test[2]}')
    total = train_val_test[0] + train_val_test[1] + train_val_test[2]
    assert total == 1, 'Train, Validation and Test split does not sum to 1'
    #img_captions = get_flickr8k_captions()
    img_captions = pd.read_csv(os.path.join(DOWNLOAD_DIRECTORY, DEST_DIRECTORY,'captions.txt'))
    image_map = {}
    #print(img_captions)
    for i in range(img_captions.shape[0]):
        img, caption = img_captions.iloc[i,0], img_captions.iloc[i,1]
        if img in image_map:
            image_map[img].append(caption)
        else:
            image_map[img] = [caption]
        
    rng = np.random.default_rng()
    keys = np.array(list(image_map.keys()))
    rng.shuffle(keys)
    train_index = int(train_val_test[0] * len(keys))
    val_index = train_index + int(train_val_test[1] * len(keys))
    train_split = keys[:train_index]
    val_split = keys[train_index:val_index]
    test_split = keys[val_index:]

    generate_captions_file(train_split, image_map, 'captions_train.txt')
    generate_captions_file(val_split, image_map, 'captions_val.txt')
    generate_captions_file(test_split, image_map, 'captions_test.txt')

def generate_captions_file(dataset_keys, image_map, name):
    lines = []
    for k in dataset_keys:
        for c in image_map[k]:
            lines.append((k,c))
    df = pd.DataFrame(lines, columns=['image','caption'])
    df.to_csv(os.path.join(DOWNLOAD_DIRECTORY, DEST_DIRECTORY, name),index=False)
    # with open(os.path.join(DOWNLOAD_DIRECTORY, DEST_DIRECTORY, name), 'w') as f:
    #     f.writelines(lines)
    



    








'''
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
                                                Flickr Dataset
'''

class FlickrDataset(Dataset):

    def __init__(self,root_dir,captions_file,transform=None):
        self.root_dir = root_dir
        self.df = pd.read_csv(captions_file)
        self.transform = transform
        
        #Get image and caption colum from the dataframe
        self.imgs = self.df["image"]
        self.captions = self.df["caption"]

        #Preprocess the captions
        self.vocab = v.Vocabulary(vocab_file='vocab.pkl',vocab_from_file=True)
        self.caption_preprocessor = captionPreprocessing.CaptionProprocessor()
        self.max_caption_length = self.caption_preprocessor.max_Caption_Length(self.captions)

        
        #Initialize vocabulary and build vocab
        self.vocab = v.Vocabulary(vocab_file='vocab.pkl',vocab_from_file= True)
        
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self,index):
        caption = self.captions[index]
        img_name = self.imgs[index]
        img_location = os.path.join(self.root_dir,img_name)
        img = Image.open(img_location).convert("RGB")
        
        #apply the transformation to the image
        if self.transform is not None:
            img = self.transform(img)
        
        # Convert caption to indices
        caption_vec = self.caption_preprocessor.convertCaptionToIndices(caption,self.max_caption_length,self.vocab)
        
        return img, torch.tensor(caption_vec)
    

def get_loader(root_folder,captions_file,transform,batch_size=32,num_workers=2,shuffle=True):
    dataset = FlickrDataset(root_folder,captions_file,transform)
    data_loader = torch.utils.data.DataLoader(dataset=dataset,
                                              batch_size=batch_size,
                                              shuffle=shuffle,
                                              num_workers=num_workers)
    return dataset , data_loader




'''
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
##################################################################################################################################
                                                Old Flickdataset (used in encoder.py)
'''


class ImageDataset(Dataset):
    def __init__(self, img_captions, img_size=(224,224), root=None):
        super().__init__()
        self.device = get_default_device()
        self.root = os.path.join(DOWNLOAD_DIRECTORY, DEST_DIRECTORY, 'Images') if root is None else root
        
        #initializing the transformation set with the default conversion
        self.img_captions = img_captions # [(img_name, caption),(img_name, caption)]
        self.default_transformation = transforms.Compose(
            [
                transforms.Resize(img_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ]
        )

    def __len__(self):
        return len(self.img_captions)

    def __getitem__(self, index):
        #print(index)
        img_path = os.path.join(self.root, self.img_captions[index][0])
        caption = self.img_captions[index][1]
        image = Image.open(img_path).convert('RGB')
        return self.default_transformation(image), caption
      
def get_flickr8k_captions(captions_path=None, skip_rows=1):
    if captions_path is None:
        captions_path = os.path.join(DOWNLOAD_DIRECTORY, DEST_DIRECTORY,'captions.txt')
    captions = []
    with open(captions_path, 'r') as caption_file:
        captions = caption_file.readlines()
    
    captions = [c.strip('\n').split(',') for c in captions[skip_rows:]]
    return captions


device = get_default_device()
# Download and unzip the ZIP file
print(download_and_unzip(DATASET, DOWNLOAD_DIRECTORY, DEST_DIRECTORY))
# data_split()


if __name__ =='__main__':
    pass