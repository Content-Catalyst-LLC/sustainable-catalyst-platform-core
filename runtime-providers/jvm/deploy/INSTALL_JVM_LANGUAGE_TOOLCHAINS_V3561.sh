#!/usr/bin/env bash
set -euo pipefail
ROOT="${SC_JVM_TOOLCHAIN_ROOT:-/opt/sustainable-catalyst/toolchains}"
KOTLIN_VERSION="2.4.20"
KOTLIN_SHA="59e9ca74c7904ef2c122b12114937673ccce68de820a663f0ed66ccf8799e0b7"
SCALA_VERSION="3.9.0"
KOTLIN_DIR="$ROOT/kotlin-$KOTLIN_VERSION"
SCALA_DIR="$ROOT/scala3-$SCALA_VERSION"

sudo apt-get update
sudo apt-get install -y openjdk-21-jdk-headless curl unzip tar ca-certificates
sudo mkdir -p "$ROOT"

if [[ ! -x "$KOTLIN_DIR/bin/kotlinc" ]]; then
  tmp="$(mktemp -d)";trap 'rm -rf "$tmp"' EXIT
  curl -fL --retry 3 -o "$tmp/kotlin.zip" "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip"
  echo "$KOTLIN_SHA  $tmp/kotlin.zip" | sha256sum -c -
  unzip -q "$tmp/kotlin.zip" -d "$tmp/kotlin"
  sudo rm -rf "$KOTLIN_DIR"
  sudo mv "$tmp/kotlin/kotlinc" "$KOTLIN_DIR"
fi

if [[ ! -x "$SCALA_DIR/bin/scalac" ]]; then
  tmp2="$(mktemp -d)";trap 'rm -rf "$tmp2"' EXIT
  curl -fL --retry 3 -o "$tmp2/scala.tgz" "https://github.com/scala/scala3/releases/download/${SCALA_VERSION}/scala3-${SCALA_VERSION}.tar.gz"
  SCALA_SHA="$(sha256sum "$tmp2/scala.tgz" | awk '{print $1}')"
  echo "SCALA_3_9_0_ARCHIVE_SHA256=$SCALA_SHA"
  tar -xzf "$tmp2/scala.tgz" -C "$tmp2"
  sudo rm -rf "$SCALA_DIR"
  sudo mv "$tmp2/scala3-${SCALA_VERSION}" "$SCALA_DIR"
  echo "$SCALA_SHA" | sudo tee "$SCALA_DIR/.archive-sha256" >/dev/null
fi

sudo chown -R root:root "$KOTLIN_DIR" "$SCALA_DIR"

JAVA_BIN="$(command -v java)";JAVAC_BIN="$(command -v javac)"
"$JAVA_BIN" -version
"$JAVAC_BIN" -version
"$KOTLIN_DIR/bin/kotlinc" -version
"$SCALA_DIR/bin/scala" -version
"$SCALA_DIR/bin/scalac" -version

echo 'PASS - JVM Java/Kotlin/Scala toolchains installed'
