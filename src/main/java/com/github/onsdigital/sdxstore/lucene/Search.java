package com.github.onsdigital.sdxstore.lucene;


import com.github.onsdigital.sdxstore.api.ResultData;
import com.github.onsdigital.sdxstore.api.ResultList;
import com.github.onsdigital.sdxstore.json.Json;
import org.apache.commons.lang3.StringUtils;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.*;

import java.io.IOException;


/**
 * Searches for survey responses in the SDX store.
 */
public class Search {

    public static final int MAX_RESULTS = 100;

    /**
     * Gets up to {@value #MAX_RESULTS} results. All parameters can be null, depending on how you want to filter the search.
     * TODO: this will need to be increased pretty soon. We can probably repeat the search using the highest added date,
     * TODO: but will likely need to sort so that we can use this value as a form of paging.
     *
     * @param surveyId The survey ID.
     * @param formType The form type.
     * @param ruRef    The Reference Unit.
     * @param period   The survey period.
     * @param addedMs  The date to search from, in milliseconds.
     * @return The result of calling {@link IndexSearcher#search(Query, int)}.
     * @throws IOException If an {@link IndexSearcher} operation falis.
     */
    public static ResultList get(String surveyId, String formType, String ruRef, String period, String addedMs) throws IOException {

        // Search
        try (IndexReader indexReader = SdxStore.indexReader()) {
            IndexSearcher indexSearcher = new IndexSearcher(indexReader);
            Query query = buildQuery(surveyId, formType, ruRef, period, addedMs);
            System.out.println("Searching for: " + query.toString());
            TopDocs topDocs = indexSearcher.search(query, MAX_RESULTS);

            // Results
            ResultList resultList = new ResultList();
            resultList.totalHits = topDocs.totalHits;
            ScoreDoc[] scoreDocs = topDocs.scoreDocs;
            for (ScoreDoc scoreDoc : scoreDocs) {
                ResultData resultData = new ResultData();
                Document document = indexSearcher.doc(scoreDoc.doc);
                resultData.addedDate = document.get(SdxStore.addedDate);
                resultData.addedMs = document.get(SdxStore.addedMs);
                resultData.surveyResponse = Json.parse(document.get(SdxStore.surveyResponse));
                resultList.results.add(resultData);
            }

            return resultList;
        }
    }

    /**
     * Builds a search query from the given values, which can be null.
     * @param surveyId The survey ID.
     * @param formType The form type.
     * @param ruRef    The Reference Unit.
     * @param period   The survey period.
     * @param addedMs  The date to search from, in milliseconds.
     * @return A query specifying that all non-blank values must be present and that the {@code addedMs} must be
     * greater than or equal to the given value (if present).
     */
    private static Query buildQuery(String surveyId, String formType, String ruRef, String period, String addedMs) {

        BooleanQuery.Builder builder = new BooleanQuery.Builder();

        // Add the specified search terms
        addField(SdxStore.surveyId, surveyId, builder);
        addField(SdxStore.formType, formType, builder);
        addField(SdxStore.ruRef, ruRef, builder);
        addField(SdxStore.period, period, builder);

        // Add the "since" filter, if specified
        if (StringUtils.isNumeric(period)) {
            TermRangeQuery rangeQuery = TermRangeQuery.newStringRange(SdxStore.addedMs, addedMs, "*", true, true);
            builder.add(rangeQuery, BooleanClause.Occur.MUST);
        }

        return builder.build();
    }

    /**
     * Adds a {@link TermQuery} to the given {@link BooleanQuery.Builder}.
     *
     * @param name    The field name.
     * @param value   The search term.
     * @param builder The builder to add to.
     */
    private static void addField(String name, String value, BooleanQuery.Builder builder) {
        if (StringUtils.isNotBlank(value)) {
            TermQuery termQuery = new TermQuery(new Term(name, value));
            builder.add(termQuery, BooleanClause.Occur.MUST);
        }
    }

}
