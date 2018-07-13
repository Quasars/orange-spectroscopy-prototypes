if [ "$PYQT5" ]; then
    # 20180124 force 5.9.2 due to segfaults on new 5.10
    pip install sip pyqt5==5.9.2
    return $?;
fi

PYQT=$TRAVIS_BUILD_DIR/pyqt

SIP_VERSION=4.16.9
PYQT_VERSION=4.11.4

if [ ! "$(ls $PYQT)" ]; then
    mkdir -p $PYQT
    cd $PYQT

    wget -O sip.tar.gz http://sourceforge.net/projects/pyqt/files/sip/sip-$SIP_VERSION/sip-$SIP_VERSION.tar.gz
    mkdir -p sip
    tar xzf sip.tar.gz -C sip --strip-component=1

    wget -O PyQt.tar.gz  http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-$PYQT_VERSION/PyQt-x11-gpl-$PYQT_VERSION.tar.gz
    mkdir -p PyQt
    tar xzf PyQt.tar.gz -C PyQt --strip-components=1

    cd $PYQT/sip
    python configure.py -e $PYQT/include
    make
    make install

    cd $PYQT/PyQt
    pwd
    python configure.py --confirm-license --no-designer-plugin
    make
fi

cd $PYQT/sip
make install

cd $PYQT/PyQt
make install

cd $TRAVIS_BUILD_DIR
