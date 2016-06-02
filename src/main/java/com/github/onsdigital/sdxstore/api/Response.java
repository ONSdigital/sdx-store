package com.github.onsdigital.sdxstore.api;

import com.github.davidcarboni.ResourceUtils;
import com.github.davidcarboni.restolino.framework.Api;
import com.github.davidcarboni.restolino.json.Serialiser;
import com.github.onsdigital.sdxstore.json.Json;
import com.github.onsdigital.sdxstore.lucene.Search;
import com.github.onsdigital.sdxstore.lucene.Store;
import com.google.gson.JsonElement;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import java.io.IOException;
import java.util.regex.Pattern;

/**
 * API for storing and retrieving responses.
 */
@Api
public class Response {

    Pattern valid = Pattern.compile("[a-zA-Z0-9]+");

    @POST
    public void store(HttpServletRequest request, HttpServletResponse response) throws IOException {
        JsonElement json = Json.parse(request.getInputStream());
        Store.add(json);
    }

    @GET
    public JsonElement retrieve(HttpServletRequest request) {
        Search.get();
    }

    public static void main(String[] args) throws IOException {
        JsonElement element = Json.parse(ResourceUtils.getStream("/test.json"));
        System.out.println(Serialiser.serialise(element));
    }
}
