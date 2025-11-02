#!/bin/bash 

VIDEO_DIR="/home/sultan/signage/media/video" 

while true; do 
  for video in "$VIDEO_DIR"/; do 
    mpv "$video" --fs --no-border --no-window-dragging --cursor-autohide=always --loop-playlist=yes --image-display-duration=5
  done 
done 
