package com.github.onsdigital.sdxstore.lucene;

import com.github.davidcarboni.ResourceUtils;
import com.github.davidcarboni.argonaut.Argonaut;
import com.github.davidcarboni.argonaut.Json;
import com.google.gson.JsonElement;
import org.apache.commons.lang3.StringUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.*;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.store.Directory;

import java.io.IOException;
import java.util.Date;

import static com.github.onsdigital.sdxstore.lucene.SdxStore.*;
import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;

/**
 * Stores Json.
 */
public class Store {

    private static IndexWriter indexWriter;
    private static Store instance;

    public static void add(JsonElement json) throws IOException {
        if (instance == null) {
            instance = new Store();
        }
        instance.index(json);
    }

    void index(JsonElement json) throws IOException {
        Document document = document(json);
        indexWriter().addDocument(document);
        indexWriter().commit();
    }

    /**
     * Creates a new Lucene {@link Document} to store the Json survey response.
     *
     * @param json The Json to be stored.
     * @return A {@link Document} containing the Json.
     */
    Document document(JsonElement json) {
        Document document = new Document();
        Argonaut argonaut = new Argonaut(json);

        // Identifying coordinates
        addField(document, surveyId, argonaut);
        addField(document, formType, argonaut);
        addField(document, ruRef, argonaut);

        // Raw Json
        document.add(new TextField(SdxStore.response, json.toString(), Field.Store.YES));

        // Added date in searchable and viewable formats - rudimentary metadata.
        Date date = new Date();
        document.add(new LongPoint(addedMs, date.getTime()));
        document.add(new StringField(addedDate, date.toString(), Field.Store.YES));

        return document;
    }

    /**
     * Adds a {@link Field} to the lucene {@link Document}.
     *
     * @param document The {@link Document} to add the {@link Field} to.
     * @param path     The path in the Json to use as the value of the field.
     * @param argonaut An {@link Argonaut} instance for accessing the Json.
     */
    void addField(Document document, String path, Argonaut argonaut) {
        String value = StringUtils.defaultIfBlank(argonaut.stringAt(path), "");
        document.add(new StringField(path, value, Field.Store.YES));
    }

    /**
     * Lazily instantiates a singleton {@link IndexWriter}. The Lucene docs make it clear that this class is threadsafe.
     * <p>
     * NB There's a small chance of more than one {@link IndexWriter} being created, but this isn't an issue for Lucene.
     *
     * @return A singleton {@link IndexWriter}.
     * @throws IOException If an error occurs in opening the {@link Directory} or {@link IndexWriter}.
     */
    IndexWriter indexWriter() throws IOException {

        if (indexWriter == null) {

            Directory dir = SdxStore.directory();
            Analyzer analyzer = new StandardAnalyzer();
            IndexWriterConfig iwc = new IndexWriterConfig(analyzer);
            iwc.setOpenMode(CREATE_OR_APPEND);

            indexWriter = new IndexWriter(dir, iwc);

            // Shutdown hook for indexWriter
            Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        if (indexWriter != null) {
                            indexWriter.close();
                        }
                    } catch (IOException e) {
                        // TODO: logging.
                        e.printStackTrace();
                    }
                }
            }));
        }

        return indexWriter;
    }
}
