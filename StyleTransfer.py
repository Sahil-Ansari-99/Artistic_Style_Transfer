import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image
import os
import psutil


class NST:
    def __init__(self):
        self.style_predict_path = 'style_predict.tflite'
        self.style_transform_path = 'style_transform.tflite'
        self.style_image_path = 'vassily_kandinsky.jpg'
        self.content_image_path = 'eiffel_tower.jpg'
        self.style_img_target_dim = 256
        self.content_img_target_dim = 384
        self.blending_ratio = 0.02
        self.client_port = 'none'

    def set_style_img(self, path):
        self.style_image_path = path

    def set_content_img(self, path):
        self.content_image_path = path

    def set_client_port(self, port):
        self.client_port = port

    def load_image(self, path_to_img):
        img = tf.io.read_file(path_to_img)
        img = tf.io.decode_image(img, channels=3)
        img = tf.image.convert_image_dtype(img, tf.float32)
        img = img[tf.newaxis, :]
        return img

    def preprocess_image(self, image, target_dim):
        # Resize the image so that the shorter dimension becomes 256px.
        shape = tf.cast(tf.shape(image)[1:-1], tf.float32)
        short_dim = min(shape)
        scale = target_dim / short_dim
        new_shape = tf.cast(shape * scale, tf.int32)
        image = tf.image.resize(image, new_shape)
        # Central crop the image.
        image = tf.image.resize_with_crop_or_pad(image, target_dim, target_dim)
        return image

    def show_image(self, image, title=None):
        if len(image.shape) > 3:
            image = tf.squeeze(image, axis=0)
        plt.axis('off')
        plt.imshow(image)
        if title:
            plt.title(title)
        plt.show()

    def save_image(self, image, file_name):
        if len(image.shape) > 3:
            image = tf.squeeze(image, axis=0)
        plt.axis('off')
        plt.imshow(image)
        plt.savefig(file_name, bbox_inches='tight')

    def memory_usage(self):
        process = psutil.Process(os.getpid())
        mem = process.memory_info()[0] / float(2 ** 20)
        print('Memory usage:', mem, 'MB')

    def run_style_predict(self, preprocessed_style_image):
        # Load the model.
        interpreter = tf.lite.Interpreter(model_path=self.style_predict_path)
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

    def run_style_transform(self, style_bottleneck, preprocessed_content_image):
        # Load the model.
        interpreter = tf.lite.Interpreter(model_path=self.style_transform_path)
        # Set model input.
        input_details = interpreter.get_input_details()
        interpreter.allocate_tensors()
        # Set model inputs.
        interpreter.set_tensor(input_details[0]["index"], preprocessed_content_image)
        interpreter.set_tensor(input_details[1]["index"], style_bottleneck)
        interpreter.invoke()
        # Transform content image.
        stylized_image = interpreter.tensor(interpreter.get_output_details()[0]["index"])()
        return stylized_image

    def start_style_transfer(self):
        style_image = self.load_image(self.style_image_path)
        content_image = self.load_image(self.content_image_path)
        style_image = self.preprocess_image(style_image, self.style_img_target_dim)
        content_image = self.preprocess_image(content_image, self.content_img_target_dim)
        style_bottleneck = self.run_style_predict(style_image)
        content_bottleneck = self.run_style_predict(self.preprocess_image(content_image, self.style_img_target_dim))
        blended_bottleneck = self.blending_ratio * content_bottleneck + (1 - self.blending_ratio) * style_bottleneck
        # style_image_2 = self.load_image(self.style_image_path)
        # style_image_2 = self.preprocess_image(style_image_2, self.content_img_target_dim)
        stylized_image = self.run_style_transform(blended_bottleneck, content_image)
        save_name = f'res_{self.client_port}.jpg'
        self.save_image(stylized_image, save_name)
        self.show_image(stylized_image)
        self.memory_usage()
        if os.path.isfile(save_name):
            return True
        else:
            return False


if __name__ == '__main__':
    obj = NST()
    obj.start_style_transfer()
