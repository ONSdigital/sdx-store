package com.github.onsdigital.sdxstore.api;

import com.github.davidcarboni.restolino.framework.Api;
import com.github.davidcarboni.restolino.helpers.QueryString;
import com.github.onsdigital.sdxstore.json.Argonaut;
import com.github.onsdigital.sdxstore.lucene.SdxStore;
import com.github.onsdigital.sdxstore.lucene.Search;
import com.github.onsdigital.sdxstore.lucene.Store;
import com.google.gson.JsonElement;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import java.io.IOException;
import java.net.URI;

/**
 * API for storing and retrieving survey response data.
 */
@Api
public class Response {

    //Pattern valid = Pattern.compile("[a-zA-Z0-9]+");

    @POST
    public void store(HttpServletRequest request, HttpServletResponse response) throws IOException {
        JsonElement json = Argonaut.parse(request.getInputStream());
        Store.add(json);
    }

    @GET
    public ResultList retrieve(HttpServletRequest request) throws IOException {

        // Retrieve (optional parameter values
        URI uri = URI.create(request.getRequestURL().toString()+"?"+request.getQueryString());
        QueryString queryString = new QueryString(uri);
        String surveyId = queryString.get(SdxStore.surveyId);
        String formType = queryString.get(SdxStore.formType);
        String ruRef = queryString.get(SdxStore.ruRef);
        String period = queryString.get(SdxStore.period);
        String addedMs = queryString.get(SdxStore.addedMs);

        return Search.get(surveyId, formType, ruRef, period, addedMs);
    }
}
