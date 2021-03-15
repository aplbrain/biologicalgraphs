FROM tensorflow/tensorflow:latest-gpu
WORKDIR /home
ADD . /home/biologicalgraphs

RUN apt-get update && apt-get upgrade -y && apt-get install \ 
git \
build-essentials \
lsb-release \
wget \
software-properties-common \
libcairo2-dev \
pkg-config

RUN wget -O - https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 10
ENV LLVM_CONFIG /usr/lob/llvm-10/bin/llvm-config
RUN pip install -r requirements.txt

# RUN git clone https://github.com/bjoern-andres/graph.git
# RUN pip install -r /home/biologicalgraphs/requirements.txt
# WORKDIR /home/biologicalgraphs
# RUN python algorithms/setup.py build_ext --inplace
# RUN python evaluation/setup.py build_ext --inplace
# RUN python biological/setup.py build_ext --inplace
# RUN python skeletonization/setup.py build_ext --inplace

# RUN python transforms/setup.py build_ext --inplace