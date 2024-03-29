from dataclasses import dataclass


@dataclass
class Settings:
    rulewerk_lib_path = "../lib"
    # java_home_path = "/usr/lib/jvm/java-11-openjdk-amd64" #for pk linux
    # java_home_path = "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Home"
    # java_home_path = "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Home"
    java_home_path = "C:/Program Files/Java/jdk-20" #for pk win
    souffle_master_path = "/Users/v.sinichenko/souffle/souffle-master/build/src/souffle"
    memory_measurement_interval = 0.001  # seconds; recommended value for real-life experiments: 0.5
