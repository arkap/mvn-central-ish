#!/bin/env python2

from hashlib import md5, sha1
from functools import partial
import argparse
from glob import iglob
import SimpleHTTPServer
import SocketServer
import xml.etree.ElementTree
from os import chdir

def parse_args():
	arg_parser = argparse.ArgumentParser(description="Fake a Maven central repository behavior from your local Maven repository.")
	arg_parser.add_argument("-r", dest="repo_root", action="store",
		                    help="the root of the local maven repository to be served. Defaults to '~/.m2/repository'",
		                    default="~/.m2/repository")
	arg_parser.add_argument("-p", dest="port", type=int, action="store",
		                    help="the web server's listening port", default=80)
	arg_parser.add_argument("artifacts", metavar="A", type=str, nargs="+",
		                    help="Path to maven artifacts to serve relative to repository root. (Example: com/example/artifact/1.0.0)")

	return arg_parser.parse_args()

def compute_sha1(file):
	with open(file, mode="rb") as f:
		h = sha1()
		for buf in iter(partial(f.read, 128), b""):
			h.update(buf)

	with open(file + ".sha1", mode="w") as f:
		f.write(h.hexdigest())

def compute_md5(file):
	with open(file, mode="rb") as f:
		h = md5()
		for buf in iter(partial(f.read, 128), b""):
			h.update(buf)

	with open(file + ".md5", mode="w") as f:
		f.write(h.hexdigest())

def prepare_artifacts(repo, artifacts):
	for artifact in artifacts:
		print "preparing " + artifact
		base_path = repo  + "/" + artifact
		# create maven-metadata.xml from maven-metadata-local.xml
		xmltree = xml.etree.ElementTree.parse(base_path + "/maven-metadata-local.xml")
		maven_metadata_local = xmltree.getroot()
		# remove <localCopy>true</localCopy>
		for local_copy in maven_metadata_local.findall("localCopy"):
			maven_metadata_local.remove(local_copy)

		xmltree.write(base_path + "/maven-metadata.xml")

		# compute sha1 and md5 checksum files
		compute_sha1(base_path + "/maven-metadata.xml")
		compute_md5(base_path + "/maven-metadata.xml")

		for jar in iglob(base_path + "/*.jar"):
			compute_sha1(jar)
			compute_md5(jar)

def serve_artifacts(repo_root, port):
	chdir(repo_root)

	handler = SimpleHTTPServer.SimpleHTTPRequestHandler
	httpd = SocketServer.TCPServer(("localhost", port), handler)
	print "serving artifacts at", port
	httpd.serve_forever()


if __name__ == '__main__':
	args = parse_args()
	prepare_artifacts(args.repo_root, args.artifacts)
	serve_artifacts(args.repo_root, args.port)
