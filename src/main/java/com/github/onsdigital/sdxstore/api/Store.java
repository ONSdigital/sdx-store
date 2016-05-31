package com.github.onsdigital.sdxstore.api;

import com.github.davidcarboni.ResourceUtils;
import com.github.davidcarboni.argonaut.Argonaut;
import com.github.davidcarboni.argonaut.Json;
import com.github.davidcarboni.restolino.framework.Api;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.apache.commons.lang3.StringUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.*;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.ws.rs.POST;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Calendar;
import java.util.Date;

import static com.github.onsdigital.sdxstore.api.SdxStore.*;
import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE;
import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;

/**
 * Stores Json.
 */
@Api
public class Store {

    @POST
    public void store(HttpServletRequest request, HttpServletResponse response) throws IOException {
        JsonObject json = new JsonParser().parse(new InputStreamReader(request.getInputStream())).getAsJsonObject();
    }

    public static void main(String[] args) throws IOException {

        try (IndexWriter writer = indexWriter()) {
            index(writer);
            // writer.forceMerge(1);
        }
    }

    static IndexWriter indexWriter() throws IOException {

        Directory dir = SdxStore.directory();

        Analyzer analyzer = new StandardAnalyzer();
        IndexWriterConfig iwc = new IndexWriterConfig(analyzer);
        iwc.setOpenMode(CREATE_OR_APPEND);

        return new IndexWriter(dir, iwc);
    }

    static void index(IndexWriter writer) throws IOException {

        JsonElement json = Json.parse(ResourceUtils.getString("/test.json"));
        System.out.println("adding " + json);

        Argonaut argonaut = new Argonaut(json);
        Document document = index(json, argonaut);

        //if (writer.getConfig().getOpenMode() == IndexWriterConfig.OpenMode.CREATE) {
        writer.addDocument(document);
        //} else {
        //    System.out.println("updating " + json);
        //    writer.updateDocument(new Term("path", "id"), document);
        //}
    }

    static Document index(JsonElement json, Argonaut argonaut) {
        Document document = new Document();

        // Identifying coordinates:
        index(document, surveyId, argonaut);
        index(document, formType, argonaut);
        index(document, ruRef, argonaut);

        // Raw Json:
        document.add(new TextField(SdxStore.json, json.toString(), Field.Store.YES));

        // Added date in searchable and viewable formats:
        Date date = new Date();
        document.add(new LongPoint(addedMs, date.getTime()));
        document.add(new StringField(addedDate, date.toString(), Field.Store.YES));

        return document;
    }

    static void index(Document document, String path, Argonaut argonaut) {
        String value = StringUtils.defaultIfBlank(argonaut.stringAt(path), "");
        System.out.println(path + " : " + value);
        document.add(new StringField(path, value, Field.Store.YES));
    }
}
