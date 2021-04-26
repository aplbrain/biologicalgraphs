FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04

ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && \
    apt-get install -y wget bzip2 ca-certificates curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc 

# Create the environment:
COPY requirements.txt .
RUN conda create --name biographs_env python=2.7 --file requirements.txt

# Copies source code
COPY biologicalgraphs/ /app/biologicalgraphs/

# Installs graph software
RUN mkdir /app/software/ && cd /app/software/ && git clone https://github.com/bjoern-andres/graph.git

# Build Commands
RUN echo "conda activate biographs_env" >> ~/.bashrc
SHELL ["bin/bash", "--login", "-c"]
RUN conda activate biographs_env \
    && cd /app/biologicalgraphs/algorithms && python setup.py build_ext --inplace \
    && cd /app/biologicalgraphs/evaluation && python setup.py build_ext --inplace \
    && cd /app/biologicalgraphs/graphs/biological && python setup.py build_ext --inplace \
    && cd /app/biologicalgraphs/skeletonization && python setup.py build_ext --inplace \
    && cd /app/biologicalgraphs/transforms && python setup.py build_ext --inplace

# Install pip dependencies 
RUN pip install blosc==1.4.4 intern==0.9.12

# Add source code to PATH
ENV PYTHONPATH /app:$PYTHONPATH

WORKDIR /app/biologicalgraphs/neuronseg/scripts/
ENTRYPOINT ["python", "biographs.py"]