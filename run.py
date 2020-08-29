import easyocr
reader = easyocr.Reader(['en'])
from tensorflow.keras.models import load_model
import cv2
import mysql.connector
import numpy as np
face_finder = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def f1(y_true, y_pred):
    def recall(y_true, y_pred):
        """Recall metric.

        Only computes a batch-wise average of recall.

        Computes the recall, a metric for multi-label classification of
        how many relevant items are selected.
        """
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
        recall = true_positives / (possible_positives + K.epsilon())
        return recall

    def precision(y_true, y_pred):
        """Precision metric.

        Only computes a batch-wise average of precision.

        Computes the precision, a metric for multi-label classification of
        how many selected items are relevant.
        """
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
        precision = true_positives / (predicted_positives + K.epsilon())
        return precision
    precision = precision(y_true, y_pred)
    recall = recall(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

model = load_model('my_model.h5',custom_objects={'f1': f1})

conn = mysql.connector.connect(
                            host='localhost',
                            user='root',
                            database='aadhaar_card_details',
                            charset ='utf8'
                            )
                            

def face_extractor(img):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    faces = face_finder.detectMultiScale(gray,1.3,5)
    if faces is ():
        return None
    for x,y,w,h in faces:
        cropped_image = img[y-10:y+h+15 , x-10:x+w+15]
    return cropped_image


cap = cv2.VideoCapture(1)
Gender = None
Birth = None
flag = None
Adhaar_Number = None
face = None
Name = None
while True:
    ret,frame = cap.read()
    img = frame.copy()
    img1 = frame.copy()
    frame = cv2.resize(frame,(224,224),interpolation=cv2.INTER_AREA)
    frame = frame /255
    frame = frame.reshape(1,224,224,3)
    output = model.predict_classes(frame)
    if output == [[1]]:
        img = cv2.putText(img,'Found', (30,30) , cv2.FONT_HERSHEY_COMPLEX , 1  , (0,255,0) , 2)
        cv2.imshow('webcam',img)
        
        
        for i in reader.readtext(img1):
            if i[2]>0.40 or ((i[1].replace(' ','')).isnumeric() and Adhaar_Number == None and len(i[1])==14):
                try:
                    if ((i[1].replace(' ','')).isalpha() and Name == None and (i[1].replace(' ','')).lower() not in 'governmentofindia' and len(i[1]) > 7) :
                        frame = cv2.rectangle(frame,tuple(i[0][0]),(i[0][0][0]+250,i[0][0][1]+170),(0,255,0),3)
                        Name = i[1]
                    
                except:
                    pass
                if ((i[1].replace('/',''))).isnumeric() and Birth == None and len(i[1])>= 4 and int((i[1].replace('/',''))[-4:]) < 2019 and len(i[1].replace('/','')) <=8  :
                    Birth = i[1]

                
                if ((i[1]=='Male' or i[1] == 'Female') and Gender == None) :
                    Gender = i[1]    
                
                
                if ((i[1].replace(' ','')).isnumeric() and Adhaar_Number == None and len(i[1])>=12):
                    Adhaar_Number = i[1]
                
                if face is None:
                    face = face_extractor(img1)
            
            
                if (Name != None and Gender != None and Birth != None and Adhaar_Number != None and face is not None ):
                    print(f'Name : {Name}')
                    print(f'Birth : {Birth}')
                    print(f'Gender : {Gender}')
                    print(f'Adhaar_Number : {Adhaar_Number}')
                    cv2.imshow('face',face[:,:,::-1])
                    cv2.waitKey(2000)
                    print()
                    print('is it correct??')
                    print('Enter yes or no')
                    ans = input()
                    if ans == 'yes':
                        face_encoded = cv2.imencode('.jpg', face)[1].tostring()
                        if conn.is_connected():
                            '''
                            Check if this table exits. If not, then create a new one.
                            '''
                            print('Database Connected')
                            mycursor = conn.cursor()
                            mycursor.execute("""
                                SELECT COUNT(*)
                                FROM information_schema.tables
                                WHERE table_name = 'aadhaar_card_details_table'
                                """)
                            if mycursor.fetchone()[0] != 1:
                                print('Table Not Found')
                                print('Creating New Table')
                                mycursor.execute("CREATE TABLE aadhaar_card_details_table (Aadhaar_Number VARCHAR (255) PRIMARY KEY, Name VARCHAR (255), Birth VARCHAR (255), Gender VARCHAR (255), img LONGBLOB NOT NULL)")
                                conn.commit()
                            else:
                                print('Table Found')
        
                            sql = "INSERT INTO aadhaar_card_details_table (Aadhaar_Number, Name, Birth, Gender, img) VALUES (%s, %s, %s, %s, %s)"
                            val = (Adhaar_Number, Name, Birth, Gender, face_encoded)
                            try:
                                mycursor.execute(sql, val)
                            except mysql.connector.IntegrityError:
                                print(f'{Adhaar_Number} already present')
                                print('Failed to Store in Database')
                                conn.commit()
                                mycursor.close()
                                flag = 0
                                break
                            conn.commit()
                            mycursor.close()
                            print('All Details Stored in Database')
                    
                        flag = 0
                        break
                    else:
                        Name = None
                        Birth = None
                        Gender = None
                        face = None
                        Adhaar_Number = None
    
    #cv2.imshow('web',frame)
    else:
        cv2.putText(img,'No Aadhaar Card Found', (30,30) , cv2.FONT_HERSHEY_COMPLEX , 1 , (255,0,0) , 2)
        cv2.imshow('webcam',img)
    
    

    if cv2.waitKey(1) == 13 or flag==0:  
        break
cap.release()
cv2.destroyAllWindows()

    
        
                            
                            
                         
