package com.github.onsdigital.sdxstore.lucene;

import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Provides an interface to the filesystem location of the store and standardised field names.
 */
public class SdxStore {

    /** Fields used to select a set of survey responses. */
    static String surveyId = "surveyId";
    static String formType = "formType";
    static String ruRef = "ruRef";
    static String period = "period";

    /** Field used to store the original survey response Json. */
    static String response = "response";

    /** Metadata fields. For both searching and viewing. */
    static String addedMs = "addedMs";
    static String addedDate = "addedDate";

    private static Directory dir;
    private static Path indexPath = Paths.get("sdx-store");

    static Directory directory() throws IOException {

        if (dir == null) {

            if (!Files.exists(indexPath)) {
                Files.createDirectories(indexPath);
            }
            dir = FSDirectory.open(indexPath);
        }
        return dir;
    }
}
