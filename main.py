import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image

style_predict_path = 'style_predict.tflite'
style_transform_path = 'style_transform.tflite'

style_img_path = 'vassily_kandinsky.jpg'
content_img_path = 'dog_image.jpg'

# Function to load an image from a file, and add a batch dimension.
def load_img(path_to_img):
    img = tf.io.read_file(path_to_img)
    img = tf.io.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = img[tf.newaxis, :]
    return img

# Function to pre-process by resizing an central cropping it.
def preprocess_image(image, target_dim):
    # Resize the image so that the shorter dimension becomes 256px.
    shape = tf.cast(tf.shape(image)[1:-1], tf.float32)
    short_dim = min(shape)
    scale = target_dim / short_dim
    new_shape = tf.cast(shape * scale, tf.int32)
    image = tf.image.resize(image, new_shape)
    # Central crop the image.
    image = tf.image.resize_with_crop_or_pad(image, target_dim, target_dim)
    return image

content_img = load_img(content_img_path)
style_img = load_img(style_img_path)

content_img = preprocess_image(content_img, 384)
style_img = preprocess_image(style_img, 256)

def show_image(image, title=None):
    if len(image.shape) > 3:
        image = tf.squeeze(image, axis=0)

    plt.imshow(image)
    if title:
        plt.title(title)

def run_style_predict(preprocessed_style_image):
    # Load the model.
    interpreter = tf.lite.Interpreter(model_path=style_predict_path)
    # Set model input.
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    interpreter.set_tensor(input_details[0]["index"], preprocessed_style_image)
    # Calculate style bottleneck.
    interpreter.invoke()
    style_bottleneck = interpreter.tensor(
      interpreter.get_output_details()[0]["index"]
      )()

    return style_bottleneck

style_bottleneck = run_style_predict(style_img)

# Run style transform on preprocessed style image
def run_style_transform(style_bottleneck, preprocessed_content_image):
    # Load the model.
    interpreter = tf.lite.Interpreter(model_path=style_transform_path)
    # Set model input.
    input_details = interpreter.get_input_details()
    interpreter.allocate_tensors()
    # Set model inputs.
    interpreter.set_tensor(input_details[0]["index"], preprocessed_content_image)
    interpreter.set_tensor(input_details[1]["index"], style_bottleneck)
    interpreter.invoke()

    # Transform content image.
    stylized_image = interpreter.tensor(
      interpreter.get_output_details()[0]["index"]
      )()

    return stylized_image

# stylized_image = run_style_transform(style_bottleneck, content_img)

style_bottleneck_content = run_style_predict(
    preprocess_image(content_img, 256)
    )

# Define content blending ratio between [0..1].
# 0.0: 0% style extracts from content image.
# 1.0: 100% style extracted from content image.
content_blending_ratio = 0.2

# Blend the style bottleneck of style image and content image
style_bottleneck_blended = content_blending_ratio * style_bottleneck_content + (1 - content_blending_ratio) * style_bottleneck

# Stylize the content image using the style bottleneck.
stylized_image_blended = run_style_transform(style_bottleneck_blended,
                                             content_img)

show_image(stylized_image_blended)
plt.show()
