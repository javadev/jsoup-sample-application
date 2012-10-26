package com.github.jsoup;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

public class Sample {
    public static void main(String[] args) throws Exception {
        Document doc = Jsoup.connect("http://en.wikipedia.org/").get();
    }
}
