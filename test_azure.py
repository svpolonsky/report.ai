from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
# endpoint and key
endpoint = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/'
#endpoint = 'https://northeurope.api.cognitive.microsoft.com/vision/v2.0/'
#key = 'aa80855ca8004d7aabf0a37b930c137d'
key ='0b6a3d8f5a974978ad1a7d92c5c30a57'
# Set credentials
credentials = CognitiveServicesCredentials(key)
# Create client
client = ComputerVisionClient(endpoint, credentials)


url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Broadway_and_Times_Square_by_night.jpg/450px-Broadway_and_Times_Square_by_night.jpg"

image_analysis = client.analyze_image(url,visual_features=[VisualFeatureTypes.tags])

for tag in image_analysis.tags:
    print(tag)
