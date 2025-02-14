from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rmdir
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout

import os

required_conan_version = ">=1.52.0"

class MpppConan(ConanFile):
    name = "mppp"
    description = "Multiprecision for modern C++ Topics"
    license = "MPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/bluescarni/mppp/"
    topics = ("multiprecision", "gmp", "math-bignum", "computer-algebra")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_mpfr": [True, False],
        "with_arb": [True, False],
        "with_mpc": [True, False],
        "with_quadmath": [True, False],
        "with_boost": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_mpfr": False,
        "with_arb": False,
        "with_mpc": False,
        "with_quadmath": False,
        "with_boost": False,
    }

    @property
    def _minimum_cpp_standard(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            try:
                del self.options.fPIC
            except Exception:
                pass

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("gmp/6.2.1")
        if self.options.with_mpfr == True:
            self.requires("mpfr/4.1.0")
        if self.options.with_mpc == True:
            self.requires("mpc/1.2.0")
        if self.options.with_boost == True:
            self.requires("boost/1.80.0")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        if self.options.with_arb:
            raise ConanInvalidConfiguration(f"{self.ref}:with_arb=True is not supported because `fredrik-johansson/arb` is not packaged in CCI. (yet)")
        if self.options.with_quadmath:
            raise ConanInvalidConfiguration(f"{self.ref}:with_quadmath=True is not supported because   `libquadmath` is not available from CCI. (yet)")
        if self.options.with_boost and self.options["boost"].without_serialization:
            raise ConanInvalidConfiguration(f"{self.name}:with_boost=True requires boost::without_serialization=False")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        tc.variables["MPPP_BUILD_STATIC_LIBRARY"] = not self.options.shared
        tc.variables["MPPP_WITH_MPFR"] = self.options.with_mpfr
        tc.variables["MPPP_WITH_ARB"] = self.options.with_arb
        tc.variables["MPPP_WITH_MPC"] = self.options.with_mpc
        tc.variables["MPPP_WITH_QUADMATH"] = self.options.with_quadmath
        tc.variables["MPPP_WITH_BOOST_S11N"] = self.options.with_boost
        if not self.options.shared:
            tc.variables["MPPP_BUILD_STATIC_LIBRARY_WITH_DYNAMIC_MSVC_RUNTIME"] = not is_msvc_static_runtime(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.libs = ["mp++"]
        self.cpp_info.set_property("cmake_file_name", "mp++")
        self.cpp_info.set_property("cmake_target_name", "mp++::mp++")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "mp++"
        self.cpp_info.filenames["cmake_find_package_multi"] = "mp++"
        self.cpp_info.names["cmake_find_package"] = "mp++"
        self.cpp_info.names["cmake_find_package_multi"] = "mp++"
