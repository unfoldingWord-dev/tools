FROM debian:latest

# Install packages
RUN apt update && apt install -y \
    context \
    curl \
    fonts-noto \
    pandoc \
    python \
    python-pip \
    texlive-fonts-recommended \
    texlive-xetex \
    wget

# Install python packages
RUN pip install --upgrade pip \
 && pip install \
    usfm-tools

# Download local catalog
RUN wget https://api.unfoldingword.org/uw/txt/2/catalog.json \
 && mkdir -p /var/www/vhosts/api.unfoldingword.org/httpdocs/uw/txt/2 \
 && mv catalog.json /var/www/vhosts/api.unfoldingword.org/httpdocs/uw/txt/2

# Clean up run image
RUN apt remove -y \
    wget \
 && apt-get purge -y --auto-remove \
                  -o APT::AutoRemove::RecommendsImportant=false \
 && rm -rf /var/lib/apt/lists/* \
           /tmp/*

# Setup working volume
VOLUME "/working"

# Setup entrypoint
COPY [".", "."]
RUN chmod +x ./uwb/bible/pdf_export.sh
ENTRYPOINT ["./uwb/bible/pdf_export.sh"]
