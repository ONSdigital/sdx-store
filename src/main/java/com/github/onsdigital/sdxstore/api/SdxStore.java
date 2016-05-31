package com.github.onsdigital.sdxstore.api;

import com.github.davidcarboni.ResourceUtils;
import com.github.davidcarboni.argonaut.Argonaut;
import com.github.davidcarboni.argonaut.Json;
import com.google.gson.JsonElement;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Date;

import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE;
import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;

/**
 * Created by david on 31/05/2016.
 */
public class SdxStore {

    static String surveyId = "surveyId";
    static String formType = "formType";
    static String ruRef = "ruRef";
    static String json = "json";
    static String addedMs = "addedMs";
    static String addedDate = "addedDate";

    private static Directory dir;
    private static Path indexPath = Paths.get("target", "store");

    static Directory directory() throws IOException {

        if (dir == null) {

            boolean create = true;
            dir = FSDirectory.open(indexPath);
        }
        return dir;
    }
}
