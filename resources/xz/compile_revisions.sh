#/usr/bin/bash

COMMITS=$1


# clone XZ repository
#git clone https://git.tukaani.org/xz.git
#mv xz repository
mkdir build

# for each revision
i=1
while read p; do
 
  cd repository
 
  echo p
  
  # Discard 'changes' caused by the build process
  git stash
  
  # Checkout revision
  git checkout $p
        
  # Build the software locally
  ./autogen.sh
  ./configure --prefix="$HOME"
  make
  
  # Copy built binary to separate directory          
  mkdir ../build/$p/
  cp -r * ../build/$p
  
  cd ..
  i=$((i + 1))
done <$COMMITS

