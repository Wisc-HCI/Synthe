target_path=./pynaoqi-python2.7-2.1.4.13-mac64
all_libs="$target_path/*.dylib $target_path/*.so"
boost_libs=$target_path/libboost*.dylib

for lib in $all_libs; do
  echo "Treating $lib"
  for boost_lib in $boost_libs; do
    echo "Changing boost lib $boost_lib"
    install_name_tool -change $(basename $boost_lib) $boost_lib $lib
  done
done
