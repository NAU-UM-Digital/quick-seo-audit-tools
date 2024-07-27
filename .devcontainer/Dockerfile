# Debian dev container base
FROM debian:trixie

# Install a few base packages 
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install curl git zsh gcc

# Install neovim for an editor
RUN curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage
RUN chmod u+x nvim.appimage
RUN ./nvim.appimage --appimage-extract
RUN ./squashfs-root/AppRun --version
RUN ln -s /squashfs-root/AppRun /usr/bin/nvim

# Install common languages I want to use
RUN apt-get -y install python3-venv

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Set devcontainer user
RUN useradd -ms /bin/zsh devcontainer && usermod -aG sudo devcontainer
USER devcontainer

# Install oh-my-zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Install dotfiles
RUN git clone https://github.com/geofflambeth/dotfiles.git $HOME/.dotfiles
RUN ls $HOME/.dotfiles/
RUN /bin/bash $HOME/.dotfiles/install.sh 

# Avoid container exits
CMD ["tail", "-f", "/dev/null"]
