package com.github.onsdigital.sdxstore.api;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents a set of results returned from the SDX store.
 */
public class ResultList {

    /** The total number of hits may be greater than the number of results returned, which is limited to {@value com.github.onsdigital.sdxstore.lucene.Search#MAX_RESULTS}. */
    public int totalHits;

    public List<ResultData> results = new ArrayList<>();
}
