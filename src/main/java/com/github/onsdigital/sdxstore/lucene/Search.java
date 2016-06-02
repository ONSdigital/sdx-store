package com.github.onsdigital.sdxstore.lucene;


import com.google.gson.JsonElement;
import org.apache.commons.lang3.StringUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.queryparser.flexible.standard.QueryParserUtil;
import org.apache.lucene.queryparser.xml.builders.BooleanQueryBuilder;
import org.apache.lucene.queryparser.xml.builders.TermQueryBuilder;
import org.apache.lucene.search.*;
import org.apache.lucene.util.QueryBuilder;
import org.apache.lucene.queryparser.xml.QueryBuilderFactory;
import org.apache.lucene.store.Directory;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import static com.github.onsdigital.sdxstore.lucene.SdxStore.*;
import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;


/**
 * Created by david on 27/05/6.
 */
public class Search {

    public static JsonElement get(String surveyId, String formType, String ruRef, String period, String addedMs) {

        BooleanQuery.Builder builder = new BooleanQuery.Builder();

        // Add the specified search terms
        add(SdxStore.surveyId, surveyId, builder);
        add(SdxStore.formType, formType, builder);
        add(SdxStore.ruRef, ruRef, builder);
        add(SdxStore.period, period, builder);

        // Add the "since" filter, if specified
        if (StringUtils.isNumeric(period)) {
            TermRangeQuery rangeQuery = TermRangeQuery.newStringRange(SdxStore.addedMs, addedMs, "*", true, false);
            builder.add(rangeQuery, BooleanClause.Occur.MUST);
        }


        return null;
    }

    /**
     * Adds a {@link TermQuery} to the given {@link BooleanQuery.Builder}.
     * @param name The field name.
     * @param value The search term.
     * @param builder The builder to add to.
     */
    private static void add(String name, String value, BooleanQuery.Builder builder) {
        if (StringUtils.isNotBlank(value)) {
            TermQuery termQuery = new TermQuery(new Term(name, value));
            builder.add(termQuery, BooleanClause.Occur.MUST);
        }
    }


    /**
     * Simple command-line based search demo.
     */
    public static void main(String[] args) throws IOException, ParseException {

        try (IndexReader reader = DirectoryReader.open(SdxStore.directory())) {
            IndexSearcher searcher = new IndexSearcher(reader);
            Analyzer analyzer = new StandardAnalyzer();

            String q = "surveyId:\"023\" AND ruRef:\"1234567890\"";

            QueryParser parser = new QueryParser("ruRef", analyzer);
            QueryBuilder builder = new QueryBuilder(analyzer);
            Query booleanQuery = builder.createBooleanQuery(SdxStore.ruRef, QueryParserUtil.escape("1234567890"));
            //new TermQueryBuilder().
            //booleanQuery..

            Query query = parser.parse("1234567890");
            System.out.println("Searching for: " + query.toString("ruRef"));

            result(searcher, query);
        }
    }

    /**
     * This demonstrates a typical paging search scenario, where the search engine presents
     * pages of size n to the user. The user can then go to the next page if interested in
     * the next hits.
     * <p>
     * When the query is executed for the first time, then only enough results are collected
     * to fill 5 result pages. If the user wants to page beyond this limit, then the query
     * is executed another time and all hits are collected.
     */
    public static void result(IndexSearcher searcher, Query query) throws IOException {

        // Collect enough docs to show 5 pages
        TopDocs results = searcher.search(query, 5);
        ScoreDoc[] hits = results.scoreDocs;

        int numTotalHits = results.totalHits;
        System.out.println(numTotalHits + " total matching documents");

        int hit = 0;

        Document document = searcher.doc(hits[hit].doc);
        System.out.println(hit + 1);
        print(surveyId, document);
        print(formType, document);
        print(ruRef, document);
        print(response, document);
        print(addedDate, document);

    }

    static void print(String fieldName, Document document) {

        String value = document.get(fieldName);
        if (value != null) {
            System.out.println("   " + fieldName + ": " + value);
        }
    }


    static IndexWriter indexWriter() throws IOException {

        Directory dir = SdxStore.directory();

        Analyzer analyzer = new StandardAnalyzer();
        IndexWriterConfig iwc = new IndexWriterConfig(analyzer);
        iwc.setOpenMode(CREATE_OR_APPEND);

        return new IndexWriter(dir, iwc);
    }
}
