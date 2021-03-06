FROM arturol76/phusion-baseimage:0.11
LABEL maintainer="arturol76"

RUN apt-get -y install git wget usbutils python3-pip \
	&& pip3 install --upgrade pip

#install GOOGLE CORAL library and examples
RUN	echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list \
	&& curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
	&& apt-get update \
	&& apt-get -y install python3-edgetpu edgetpu-examples \
	&& apt-get -y dist-upgrade

#install TFlite and examples
WORKDIR /root
RUN wget https://dl.google.com/coral/python/tflite_runtime-1.14.0-cp36-cp36m-linux_x86_64.whl \
	&& pip3 install tflite_runtime-1.14.0-cp36-cp36m-linux_x86_64.whl \
	&& rm tflite_runtime-1.14.0-cp36-cp36m-linux_x86_64.whl \
	&& mkdir google-coral && cd google-coral \
	&& git clone https://github.com/google-coral/tflite --depth 1 \
	&& cd tflite/python/examples/detection \
	&& ./install_requirements.sh

#download yolo weights (to be used with cvlib)
RUN mkdir -p /root/.cvlib/object_detection/yolo/yolov3 \
	&& cd /root/.cvlib/object_detection/yolo/yolov3 \
	&& wget https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.cfg \
	&& wget https://pjreddie.com/media/files/yolov3.weights \
	&& wget https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.txt

#download yolo weights (to be used with yolo.py)
RUN mkdir -p /app/fastapi/models \
	&& cd /app/fastapi/models \
	&& wget https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.txt \
	&& wget https://pjreddie.com/media/files/yolov3-tiny.weights \
	&& wget https://github.com/pjreddie/darknet/raw/master/cfg/yolov3-tiny.cfg \
	&& wget https://pjreddie.com/media/files/yolov3.weights \
	&& wget https://github.com/pjreddie/darknet/raw/master/cfg/yolov3.cfg \
	&& wget https://pjreddie.com/media/files/yolov3-spp.weights \
	&& wget https://github.com/pjreddie/darknet/raw/master/cfg/yolov3-spp.cfg

#IMPORTANT: without this, you may have errors whith "import cv2"
RUN apt-get update \
	&& apt-get  -y install  libsm6 libxext6 libxrender-dev \
	&& apt-get -y upgrade
	
#deploy mlapi
#refer to https://github.com/phusion/baseimage-docker#docker_single_process
RUN mkdir -p /app/mlapi
COPY ./app/mlapi /app/mlapi
WORKDIR /app/mlapi
RUN pip3 install numpy \
	&& pip3 install --upgrade numpy \
	&& pip3 install setuptools \
	&& pip3 install --upgrade setuptools \
	&& pip install -r requirements.txt \
	&& python3 adduser_cmdline.py -u arturol76 -p arturol76
RUN mkdir /etc/service/mlapi
COPY ./app/mlapi.run /etc/service/mlapi/run
RUN chmod +x /etc/service/mlapi/run
#EXPOSE 5000

#deploy python app
#refer to https://github.com/phusion/baseimage-docker#docker_single_process
RUN mkdir -p /app/fastapi
COPY ./app/fastapi /app/fastapi
WORKDIR /app/fastapi
RUN pip install -r requirements.txt
RUN mkdir /etc/service/fastapi
COPY ./app/fastapi.run /etc/service/fastapi/run
RUN chmod +x /etc/service/fastapi/run
#EXPOSE 5001

EXPOSE 5000 5001