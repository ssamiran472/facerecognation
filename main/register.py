'''This function is used for new registrations. When employees register their faces
under an organisation, this function is evoked. This function takes two inputs,
namely, 1. Organisation user_id and 2. New employee name. This function returns a str value
which is either successful or failure depending on the status of pre-processing procedure.
Also this function automatically updates any existing face embeddings and
compressed datasets of an organistion'''

# Importing all required functions
import os, shutil, pickle, tensorflow, numpy as np
from PIL import Image
from numpy import asarray
import mtcnn
import numpy
from mtcnn import MTCNN
from cv2 import cv2
from matplotlib import pyplot
from os.path import isdir
from numpy import savez_compressed
from numpy import load
from numpy import expand_dims
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
from tensorflow.keras.models import load_model as lm
# from random import choice


# Define a function to pre-process images and paths as required
def sort(folder, train, test):
    n_images = os.listdir(folder)
    if len(n_images) < 10:
        img = cv2.imread(folder+str(n_images[0]), 1)
        n = 10-(10-len(n_images))+1
        for i in range(n, 13):
            cv2.imwrite(folder+str(i)+'.jpg', img)
    elif len(n_images) > 10:
        pass
    _ = os.listdir(folder)
    for i, m in enumerate(_):
        if i <= 9:
            shutil.move(folder+m, train+m)
        else:
            shutil.move(folder+m, test+m)
    os.rmdir(folder)
    return 'Data ready for input'

# extract a single face from a given photograph
def extract_face(filename, required_size=(160, 160)):
    # load image from file
    image = Image.open(filename)
    # convert to RGB, if needed
    image = image.convert('RGB')
    # convert to array
    pixels = asarray(image)
    # create the detector, using default weights
    det = MTCNN()
    detector = MTCNN()
    # detect faces in the image
    results = detector.detect_faces(pixels)
    # extract the bounding box from the first face
    x1, y1, width, height = results[0]['box']
    # bug fix
    x1, y1 = abs(x1), abs(y1)
    x2, y2 = x1 + width, y1 + height
    # extract the face
    face = pixels[y1:y2, x1:x2]
    # resize pixels to the model size
    image = Image.fromarray(face)
    image = image.resize(required_size)
    face_array = asarray(image)
    return face_array
 
# load images and extract faces for all images in a directory
def load_faces(directory):
    faces = list()
    # enumerate files
    for filename in os.listdir(directory):
        # path
        path = directory + filename
        # get face
        face = extract_face(path)
        # store
        faces.append(face)
    return faces
 
# load a dataset that contains one subdir for each class that in turn contains images
def load_dataset(directory, name):
    X, y = list(), list()
    # path
    path = directory 
    # load all faces in the subdirectory
    faces = load_faces(path)
    # create labels
    labels = [name for _ in range(len(faces))]
    # store
    X.extend(faces)
    y.extend(labels)
    return asarray(X), asarray(y)
 
# Define a function to load new images and update existing dataset
def update_data(path, train, test, name):
    # extract new train dataset
    trainX, trainy = load_dataset(train, name)
    # extract new test dataset
    testX, testy = load_dataset(test, name)
    #Load old dataset
    data = load(path+'/Data/employees/dataset.npz')
    trXo, tryo, teXo, teyo = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    # Update the old dataset with new employee data
    trxn = np.concatenate((trXo, trainX), axis=0)
    tryn = np.concatenate((tryo, trainy), axis=0)
    texn = np.concatenate((teXo, testX), axis=0)
    teyn = np.concatenate((teyo, testy), axis=0)
    # Upadte data arrays to one file in compressed format
    savez_compressed(path+'/Data/employees/temp.npz', trainX, trainy, testX, testy)
    savez_compressed(path+'/Data/employees/dataset.npz', trxn, tryn, texn, teyn)
    return "Dataset successfully updated"

def update_faces(path):
    def get_embedding(model, face_pixels):
        # scale pixel values
        face_pixels = face_pixels.astype('float32')
        # standardize pixel values across channels (global)
        mean, std = face_pixels.mean(), face_pixels.std()
        face_pixels = (face_pixels - mean) / std
        # transform face into one sample
        samples = expand_dims(face_pixels, axis=0)
        # make prediction to get embedding
        yhat = model.predict(samples)
        return yhat[0]

    data = load(path+'/Data/employees/temp.npz')
    trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    # load the facenet model
    # facenet = './models/embedder/facenet.pkl'
    # infile = open(facenet, 'rb')
    # model = pickle.load(infile)
    # infile.close()
    model=lm('/var/www/djangomac/facerecognation/models/embedder/facenet.h5')
    # convert each face in the train set to an embedding
    newTrainX = list()
    for face_pixels in trainX:
        embedding = get_embedding(model, face_pixels)
        newTrainX.append(embedding)
    newTrainX = asarray(newTrainX)
    # print(newTrainX.shape)
    # convert each face in the test set to an embedding
    newTestX = list()
    for face_pixels in testX:
        embedding = get_embedding(model, face_pixels)
        newTestX.append(embedding)
    newTestX = asarray(newTestX)
    # Load previously saved embeddings
    data = load(path+'/Data/employees/embeddings.npz')
    trXo, tryo, teXo, teyo = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    # Update the 128-D face vectors
    trxn = np.concatenate((trXo, newTrainX), axis=0)
    tryn = np.concatenate((tryo, trainy), axis=0)
    texn = np.concatenate((teXo, newTestX), axis=0)
    teyn = np.concatenate((teyo, testy), axis=0)
    # save arrays to one file in compressed format
    savez_compressed(path+'/Data/employees/embeddings.npz', trxn, tryn, texn, teyn)
    os.remove(path+'/Data/employees/temp.npz')
    return "Vectors updated successfully"


# Create a new svc model and fit updated data to learn new weights
def classifier(path, user, acc=False):
    # Load faces
    data = load(path+'/Data/employees/dataset.npz')
    testX_faces = data['arr_2']
    # Load embeddings
    data = load(path+'/Data/employees/embeddings.npz')
    trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    # Normalize input vectors
    in_encoder = Normalizer(norm='l2')
    trainX = in_encoder.transform(trainX)
    testX = in_encoder.transform(testX)
    # Label encode targets
    out_encoder = LabelEncoder()
    out_encoder.fit(trainy)
    trainy = out_encoder.transform(trainy)
    testy = out_encoder.transform(testy)
    # Fit model
    svc = SVC(kernel='linear', probability=True)
    svc.fit(trainX, trainy)
    # Serialize the SVC model and label encoded classes for verification.py
    from joblib import dump
    m = "/var/www/djangomac/facerecognation/media/documents/"+user+"/classifier/classifier.joblib"
    with open(m, 'wb') as file:
        dump(svc, file)
    numpy.save('/var/www/djangomac/facerecognation/media/documents/'+user+'/encoder/classes.npy', out_encoder.classes_)
    # ****************For accuracy issues and debugging only****************
    # if acc == True:
    #     from sklearn.metrics import accuracy_score as ac
    #     preds = svc.predict(testX)
    #     ___ = ac(testy, preds)*100
    #     score = round((___, 2)
    #     return score
    # else:
    return("Model Updated Successfully")

# Register function called directly from the frontend register button
def register(org_id, employee_name):
    # Define absolute path
    path = "/var/www/djangomac/facerecognation/media/documents/"+str(org_id)
    # Check for parallel processing
    try:
        from .dummy import dummy
        # Change the dummy function
        os.rename('/var/www/djangomac/facerecognation/main/dummy.py', '/var/www/djangomac/facerecognation/main/wait.py')
        # Create train/test directories for new registrants
        os.mkdir(path+'/Data/train/'+employee_name)
        os.mkdir(path+'/Data/test/'+employee_name)
        # print("User already registered, same name exists in data base")
        # Define static image and new train/test folder paths for registrant
        folder = path+"/static/"+str(employee_name)+"/"
        train = path+"/Data/train/"+employee_name+'/'
        test = path+"/Data/test/"+employee_name+'/'
        # Call the pre-defined function to prep-images for input
        se = sort(folder, train, test)
        # Update the dataset for new employees data
        ude = update_data(path, train, test, name=employee_name)
        # Update 128-D Face Vectors
        ufe = update_faces(path)
        # Update the classifier model
        ucm = classifier(path, user=org_id)
        # Revert the dummy function
        os.rename('/var/www/djangomac/facerecognation/main/wait.py', '/var/www/djangomac/facerecognation/main/dummy.py')
        # Check for errors
        if se == 'Data ready for input':
            o = True
        if ude == "Dataset successfully updated":
            t = True
        if ufe == "Vectors updated successfully":
            th = True
        if ucm == "Model Updated Successfully":
            um = True
        if o & t & th & um == True:
            return "Registration Successful"
        else:
            return "Registration Failed"
    except ImportError:
        return "Server currently busy"
        pass
        
if __name__ == "__main__":
    register()
