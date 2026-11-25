package dev.syncidea.lab.names;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.parallel.ResourceLock;
import org.junit.jupiter.api.parallel.Resources;

class UsernameNormalizerTest {
    @Test
    void stripsEdgesAndLowercasesName() {
        assertEquals("alice-42", UsernameNormalizer.normalize("  Alice-42  "));
    }

    @Test
    void preservesInnerSpacingAndPunctuation() {
        assertEquals("анна  иванова-7", UsernameNormalizer.normalize(" Анна  ИВАНОВА-7 "));
        assertEquals("a\tb", UsernameNormalizer.normalize("\tA\tB\n"));
    }

    @Test
    void stripsUnicodeWhitespaceAccordingToStringStrip() {
        assertEquals("bob", UsernameNormalizer.normalize("\u2003BOB\u2003"));
    }

    @Test
    void handlesEmptyAndBlankInput() {
        assertEquals("", UsernameNormalizer.normalize(""));
        assertEquals("", UsernameNormalizer.normalize(" \t\n\u2003"));
    }

    @Test
    @ResourceLock(Resources.LOCALE)
    void doesNotInheritTurkishCaseRulesFromMachine() {
        Locale previous = Locale.getDefault();
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"));
            assertEquals("idea", UsernameNormalizer.normalize(" IDEA "));
        } finally {
            Locale.setDefault(previous);
        }
    }

    @Test
    void rejectsNullName() {
        assertThrows(NullPointerException.class, () -> UsernameNormalizer.normalize(null));
    }
}
