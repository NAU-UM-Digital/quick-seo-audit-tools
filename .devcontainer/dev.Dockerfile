# Ubuntu image base
FROM ubuntu:latest

# Install a few base packages 
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install sudo curl wget build-essential ripgrep libreadline-dev unzip git zsh gcc

# Install neovim for CLI editors
RUN curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage
RUN chmod u+x nvim.appimage
RUN ./nvim.appimage --appimage-extract
RUN ./squashfs-root/AppRun --version
RUN ln -s /squashfs-root/AppRun /usr/bin/nvim

# Install lua itself
RUN curl -R -O https://www.lua.org/ftp/lua-5.3.5.tar.gz
RUN tar -zxf lua-5.3.5.tar.gz
RUN cd lua-5.3.5 && make linux test && make install

# Install luarocks pkg manager for neovim
RUN curl -R -O http://luarocks.github.io/luarocks/releases/luarocks-3.11.1.tar.gz
RUN tar -zxf luarocks-3.11.1.tar.gz
RUN cd luarocks-	3.11.1 && ./configure --with-lua-include=/usr/local/include && make && make install

# Install pandoc 2.19.2
RUN curl -LO https://github.com/jgm/pandoc/releases/download/2.19.2/pandoc-2.19.2-1-amd64.deb
RUN dpkg -i pandoc*.deb && rm *.deb

# Install common languages I want to use
RUN apt-get -y install python3-venv

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Install oh-my-zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Avoid container exits
CMD ["tail", "-f", "/dev/null"]
