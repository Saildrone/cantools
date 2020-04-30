load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def bazel_repos(**kwargs):
    http_archive(
        name = "rules_python",
        urls = ["https://github.com/bazelbuild/rules_python/archive/a0fbf98d4e3a232144df4d0d80b577c7a693b570.zip"],
        strip_prefix = "rules_python-a0fbf98d4e3a232144df4d0d80b577c7a693b570",
        sha256 = "98c9b903f6e8fe20b7e56d19c4822c8c49a11b475bd4ec0ca6a564e8bc5d5fa2",
    )

def googletest_repos(**kwargs):
    http_archive(
        name = "com_google_googletest",
        urls = [
            "http://sourcerepo.vehicle.saildrone.com.s3.amazonaws.com/third_party/googletest/e9d5f427b56ae62a18efafa8ec631ad177a5a83c.zip",
            "https://github.com/google/googletest/archive/e9d5f427b56ae62a18efafa8ec631ad177a5a83c.zip",
        ],
        strip_prefix = "googletest-e9d5f427b56ae62a18efafa8ec631ad177a5a83c",
        sha256 = "4ab3932e8621c6bf7b4cd2bf503e4fb1d35300d2464d1d7832a38b4b7b23505a",
    )

def cantools_repos(**kwargs):
    bazel_repos()
    googletest_repos()
