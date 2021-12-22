SSH_COMMAND="ssh -i /home/pi/.ssh/newtoy_photo_dropoff"
SOURCE="/var/photos/"
DESTINATION="/media/backup/photo_dropoff"
REMOTE_HOST="photo_dropoff@newtoy.fritz.box"

rsync -c -e "$SSH_COMMAND" --progress \
	--remove-source-files --filter "- *.jpg" -r \
	$SOURCE $REMOTE_HOST:$DESTINATION

if [[ $? == 0 ]] ; then
	echo "Success"
else
	echo "Failure"
fi
