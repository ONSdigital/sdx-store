package com.github.onsdigital.sdxstore.lucene;

import com.github.onsdigital.sdxstore.json.Json;
import com.google.gson.JsonElement;
import org.apache.commons.lang3.StringUtils;
import org.apache.lucene.document.*;
import org.apache.lucene.index.IndexWriter;

import java.io.IOException;
import java.util.Date;

import static com.github.onsdigital.sdxstore.lucene.SdxStore.*;

/**
 * Stores Json.
 */
public class Index {

    private static Index instance;

    public static void add(JsonElement surveyResponse) throws IOException {
        if (instance == null) {
            instance = new Index();
        }
        instance.index(surveyResponse);
    }

    void index(JsonElement surveyResponse) throws IOException {
        Document document = document(surveyResponse);
        IndexWriter indexWriter = SdxStore.indexWriter();
        indexWriter.addDocument(document);
        indexWriter.commit();
    }

    /**
     * Creates a new Lucene {@link Document} to store the Json survey response.
     *
     * @param surveyResponse The survey response Json to be stored.
     * @return A {@link Document} containing the Json.
     */
    Document document(JsonElement surveyResponse) {
        Document document = new Document();
        Json json = new Json(surveyResponse);

        // Identifying coordinates
        addField(document, surveyId, json);
        addField(document, formType, json);
        addField(document, ruRef, json);

        // Json survey response
        document.add(new TextField(SdxStore.surveyResponse, surveyResponse.toString(), Field.Store.YES));

        // Added date in searchable and viewable formats - rudimentary metadata.
        Date date = new Date();
        document.add(new StringField(addedMs, String.valueOf(date.getTime()), Field.Store.YES));
        document.add(new StringField(addedDate, date.toString(), Field.Store.YES));

        return document;
    }

    /**
     * Adds a {@link Field} to the lucene {@link Document}.
     *
     * @param document The {@link Document} to add the {@link Field} to.
     * @param path     The path in the Json to use as the value of the field.
     * @param json An {@link Json} instance for accessing the Json.
     */
    void addField(Document document, String path, Json json) {
        String value = StringUtils.defaultIfBlank(json.stringAt(path), "");
        document.add(new StringField(path, value, Field.Store.YES));
    }
}
