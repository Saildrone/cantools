load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def bazel_repos(**kwargs):
    http_archive(
        name = "rules_python",
        urls = ["https://github.com/bazelbuild/rules_python/archive/a0fbf98d4e3a232144df4d0d80b577c7a693b570.zip"],
        strip_prefix = "rules_python-a0fbf98d4e3a232144df4d0d80b577c7a693b570",
        sha256 = "98c9b903f6e8fe20b7e56d19c4822c8c49a11b475bd4ec0ca6a564e8bc5d5fa2",
    )

def cantools_repos(**kwargs):
    bazel_repos()
