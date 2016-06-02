package com.github.onsdigital.sdxstore.lucene;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;

/**
 * Provides an interface to the filesystem location of the store and standardised field names.
 */
public class SdxStore {

    /** Fields used to select a set of survey responses. */
    public static final String surveyId = "surveyId";
    public static final String formType = "formType";
    public static final String ruRef = "ruRef";
    public static final String period = "period";

    /** Field used to store the original survey response Json. */
    public static final String response = "response";

    /** Metadata fields. For both searching and viewing. */
    public static final String addedMs = "addedMs";
    public static final String addedDate = "addedDate";

    private static DirectoryReader indexReader;
    private static IndexWriter indexWriter;

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

    /**
     * Lazily instantiates a singleton {@link IndexReader} if needed (the Lucene docs make it clear that this class is threadsafe)
     * A new {@link IndexSearcher} is instantiated on every call which, according to the documentation, is a relatively cheap operation.
     * <p>
     * NB There's a small chance of more than one {@link IndexReader} being created, but this isn't an issue for our purposes.
     *
     * @return A new {@link IndexSearcher}.
     * @throws IOException If an error occurs in opening the {@link IndexReader} or in calling {@link #indexWriter()}.
     */
    static IndexSearcher indexSearcher() throws IOException {

        if (indexReader == null) {

            // Use a near-realtime IndexReader so we get to see updates to the index
            indexReader =  DirectoryReader.open(indexWriter());

            // Shutdown hook for indexReader
            Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        if (indexReader != null) {
                            indexReader.close();
                        }
                    } catch (IOException e) {
                        // TODO: logging.
                        e.printStackTrace();
                    }
                }
            }));
        }

        //DirectoryReader reopened = DirectoryReader.openIfChanged(indexReader);
        return new IndexSearcher(indexReader);
    }

    /**
     * Lazily instantiates a singleton {@link IndexWriter}. The Lucene docs make it clear that this class is threadsafe.
     * <p>
     * NB There's a small chance of more than one {@link IndexWriter} being created, but this isn't an issue for our purposes.
     *
     * @return A singleton {@link IndexWriter}.
     * @throws IOException If an error occurs in opening the {@link Directory} or {@link IndexWriter}.
     */
    static IndexWriter indexWriter() throws IOException {

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
