FROM tensorflow/tensorflow:latest-gpu
WORKDIR /home


RUN apt-get update && apt-get upgrade -y && apt-get install -y \ 
git \
build-essential \
lsb-release \
wget \
software-properties-common \
libcairo2-dev \
pkg-config

RUN wget -O llvm.sh https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 10
ENV LLVM_CONFIG /usr/lob/llvm-10/bin/llvm-config
ADD requirements.txt /home/biologicalgraphs/
RUN pip install -r /home/biologicalgraphs/requirements.txt

WORKDIR /home/biologicalgraphs

ADD . /home/biologicalgraphs/
WORKDIR /home/biologicalgraphs/include/
RUN git clone https://github.com/bjoern-andres/graph.git
RUN cd /home/biologicalgraphs/algorithms && python setup.py build_ext --inplace
RUN cd /home/biologicalgraphs/evaluation && python setup.py build_ext 
RUN cd /home/biologicalgraphs/graphs/biological && python setup.py build_ext --inplace
RUN cd /home/biologicalgraphs/skeletonization && python setup.py build_ext --inplace
RUN cd /home/biologicalgraphs/transforms && python setup.py build_ext --inplace