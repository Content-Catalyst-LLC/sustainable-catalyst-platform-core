#!/usr/bin/env python3
from __future__ import annotations
import os, shutil, subprocess, tempfile
from pathlib import Path

JAVA = os.environ.get("SC_JAVA_BIN", "/usr/bin/java")
JAVAC = os.environ.get("SC_JAVAC_BIN", "/usr/bin/javac")
KOTLINC = os.environ.get("SC_KOTLINC_BIN", "/opt/sustainable-catalyst/toolchains/kotlin-2.4.20/bin/kotlinc")
SCALA = os.environ.get("SC_SCALA_BIN", "/opt/sustainable-catalyst/toolchains/scala3-3.9.0/bin/scala")
SCALAC = os.environ.get("SC_SCALAC_BIN", "/opt/sustainable-catalyst/toolchains/scala3-3.9.0/bin/scalac")


def operational(cmd):
    try:
        cp = subprocess.run([cmd, "-version"], capture_output=True, text=True, timeout=15)
        return cp.returncode == 0
    except Exception:
        return False


def run(cp, label):
    if cp.returncode != 0:
        raise RuntimeError(f"{label} failed: {(cp.stderr or cp.stdout).strip()}")


def main():
    missing=[]
    for name,cmd in [("java",JAVA),("javac",JAVAC),("kotlinc",KOTLINC),("scala",SCALA),("scalac",SCALAC)]:
        if not operational(cmd): missing.append(name)
    if missing:
        print("SKIP - local JVM language toolchains unavailable: " + ",".join(missing) + "; production deployment performs mandatory profile certification")
        return
    with tempfile.TemporaryDirectory(prefix="sc-jvm-profiles-") as td:
        root=Path(td)
        # Java
        j=root/'java';j.mkdir();(j/'Main.java').write_text('public class Main { public static void main(String[] a){ System.out.println(15); } }')
        run(subprocess.run([JAVAC,'--release','21','Main.java'],cwd=j,capture_output=True,text=True), 'javac')
        cp=subprocess.run([JAVA,'-cp',str(j),'Main'],cwd=j,capture_output=True,text=True);run(cp,'java');assert cp.stdout.strip()=='15'
        print('PASS - Java 21 profile compile/run')
        # Kotlin
        k=root/'kotlin';k.mkdir();(k/'Main.kt').write_text('fun main() { println(listOf(1,2,3,4,5).sum()) }')
        run(subprocess.run([KOTLINC,'Main.kt','-include-runtime','-d','app.jar'],cwd=k,capture_output=True,text=True,timeout=120),'kotlinc')
        cp=subprocess.run([JAVA,'-jar','app.jar'],cwd=k,capture_output=True,text=True,timeout=60);run(cp,'kotlin java');assert cp.stdout.strip()=='15'
        print('PASS - Kotlin 2.4.20 profile compile/run')
        # Scala 3
        s=root/'scala';s.mkdir();(s/'Main.scala').write_text('object Main:\n  def main(args: Array[String]): Unit = println(List(1,2,3,4,5).sum)\n')
        run(subprocess.run([SCALAC,'-d',str(s),'Main.scala'],cwd=s,capture_output=True,text=True,timeout=120),'scalac')
        cp=subprocess.run([SCALA,'run','-classpath',str(s),'--main-class','Main'],cwd=s,capture_output=True,text=True,timeout=60);run(cp,'scala');assert cp.stdout.strip().splitlines()[-1]=='15'
        print('PASS - Scala 3.9.0 profile compile/run')
    print('PASS - 3/3 JVM language profiles natively certified')


if __name__ == '__main__':
    main()
