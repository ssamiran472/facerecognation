'''This function is used to run live face recognitions in order to mark attendance actively.
This function takes two inputs 1. An image frame and 2. Desired alpha value. This function automatically
detects, generates embeddings and recognizes the faces comparing it with the faces in database
and return a list of names in recognized in the input frame.'''


# Import all required libraries
from PIL import Image
from numpy import asarray
from numpy import load
from numpy import expand_dims
from mtcnn.mtcnn import MTCNN
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
import tensorflow
from tensorflow.keras.models import load_model as lm
import pickle, joblib, numpy, warnings
import tensorflow
from tensorflow.keras.models import load_model as lm
#import tensorflow.keras.backend.tensorflow_backend as tb
#tb._SYMBOLIC_SCOPE.value=True

# Ignore any unnecessary warnings
warnings.filterwarnings('ignore')

# Load all required model instances to current session
def models(user):
    # Load Facenet embedder

    #facenet = 'models/embedder/facenet.pkl'
    #infile = open(facenet, 'rb')
    #embedder = pickle.load(infile)
    #infile.close()
   # embedder = lm('/var/www/djangomac/facerecognation/models/embedder/facenet.h5')
    # Load serialized SVC model
    filename = "/var/www/djangomac/facerecognation/media/documents/"+user+"/classifier/classifier.joblib"

    with open(filename, 'rb') as m:
        svc = joblib.load(m)
    # Normalize input face vectors
    in_encoder = Normalizer(norm='l2')
    # Load label encoder classes
    out_encoder = LabelEncoder()

    out_encoder.classes_ = numpy.load('/var/www/djangomac/facerecognation/media/documents/'+user+'/encoder/classes.npy')
    return svc, in_encoder, out_encoder

# Define a function to extract_faces using the loaded model
def extract_face(frame, required_size=(160, 160)):
    detector = MTCNN()
    #print('extract_face')
    # prep image

    image = frame.convert('RGB')
    #image = frame
 

    # convert to array
    pixels = asarray(image)
    # detect faces in the image
    results = detector.detect_faces(pixels)
    print('length', len(results))
    _ = len(results)
    faces = numpy.zeros((_, 160,160,3))
    # Search for multiple faces and append as an array
    for i, m in enumerate(results):
        x1, y1, width, height = m['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        face = pixels[y1:y2, x1:x2]
        image = Image.fromarray(face)
        image = image.resize(required_size)
        faces[i] = asarray(image)
    return faces

# Define a function that extracts embeddings
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

# Define a function that returns the predicted labels and confident scores
def embedded(frame):
    #embedder, svc, in_encoder, out_encoder = models()
    print('embedded')
    imgs = extract_face(frame)
    _ = len(imgs)
    embs = numpy.zeros((_, 128))
    for i, m in enumerate(imgs):
        embs[i] = get_embedding(embedder, m)
    labels = []
    confs = []
    for i, m in enumerate(embs):
        emb = m.reshape(1, -1)
        emb = in_encoder.transform(emb)
        pred = svc.predict(emb)
        conf_ = svc.predict_proba(emb)
        l_ = (out_encoder.inverse_transform(pred))
        labels.append(l_[0])
        confs.append(conf_[0][pred[0]])
    return labels, confs


def recognize(user, frame, alpha, model):
    global embedder, svc, in_encoder, out_encoder 
    embedder = model
    print(embedder)
    svc, in_encoder, out_encoder = models(user)

    output=[]
    try:
        name, score = embedded(frame)
        for i, n in enumerate(name):
            if round(score[i]*100, 2) > alpha:
                output.append(n)
            else:
                output.append("Unknown")

    except ValueError:
        output.append("Recognizing...")
    return output


if __name__ == "__main__":
    recognize()








