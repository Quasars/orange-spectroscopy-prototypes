if [ $ORANGE_SPEC == "release" ]; then
    echo "orange-spectroscopy: Skipping separate Orange-spectroscopy install"
    return 0
fi

if [ $ORANGE_SPEC == "master" ]; then
    echo "orange-spectroscopy: from git master"
    pip install https://github.com/Quasars/orange-spectroscopy/archive/master.zip
    return $?;
fi

PACKAGE="orange-spectroscopy==$ORANGE_SPEC"
echo "Orange: installing version $PACKAGE"
pip install $PACKAGE
