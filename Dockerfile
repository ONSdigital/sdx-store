FROM java

# Add the build artifacts
WORKDIR /usr/src
#ADD git_commit_id /usr/src/
ADD ./target/*-jar-with-dependencies.jar /usr/src/target/
ADD ./startup.sh /usr/src

EXPOSE 8080

# Set the entry point
ENTRYPOINT ./startup.sh
