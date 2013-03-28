package com.github.jsoup;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import java.util.regex.Pattern;

public class Sample {
    public static void main(String[] args) throws Exception {
        Document doc = Jsoup.connect("http://polaris.umuc.edu/~sgao/BIFS618/Homework/java.txt").get();
System.out.println(doc.text());
        String[] words = Pattern.compile("\\s+").split(doc.text());
System.out.println("File has " + words.length + " words");
    }
}
