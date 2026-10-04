# ~/.bashrc (RustOS)
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias ll='ls -lah'
alias grep='grep --color=auto'
alias update='sudo pacman -Syu'
PS1='[\u@\h \W]\$ '

# Show the RustOS banner once per terminal window
if command -v fastfetch >/dev/null 2>&1 && [ -z "${RUSTOS_BANNER_DONE:-}" ]; then
  export RUSTOS_BANNER_DONE=1
  fastfetch
fi
