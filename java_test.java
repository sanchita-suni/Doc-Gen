/**
 * UserService class provides user management functionality.
 * This service handles user authentication, registration, and profile management.
 * 
 * @author Bob
 * @version 1.0
 */
public class UserService {
    
    private DatabaseConnection db;
    private Logger logger;
    
    /**
     * Authenticates a user with username and password.
     * Validates credentials against the database and returns authentication status.
     * 
     * @param username The username to authenticate
     * @param password The password to verify
     * @return true if authentication successful, false otherwise
     * @throws AuthenticationException if authentication fails
     */
    public boolean authenticateUser(String username, String password) throws AuthenticationException {
        if (username == null || password == null) {
            throw new AuthenticationException("Username and password cannot be null");
        }
        
        String hashedPassword = hashPassword(password);
        return db.verifyCredentials(username, hashedPassword);
    }
    
    /**
     * Registers a new user in the system.
     * Creates a new user account with the provided information.
     * 
     * @param username The desired username
     * @param email The user's email address
     * @param password The user's password
     * @return User object if registration successful
     * @throws RegistrationException if registration fails
     */
    public User registerUser(String username, String email, String password) throws RegistrationException {
        validateEmail(email);
        validatePassword(password);
        
        if (db.userExists(username)) {
            throw new RegistrationException("Username already exists");
        }
        
        String hashedPassword = hashPassword(password);
        return db.createUser(username, email, hashedPassword);
    }
    
    /**
     * Retrieves user profile information by user ID.
     * 
     * @param userId The unique identifier of the user
     * @return UserProfile object containing user information
     * @throws UserNotFoundException if user does not exist
     */
    public UserProfile getUserProfile(int userId) throws UserNotFoundException {
        UserProfile profile = db.findUserById(userId);
        
        if (profile == null) {
            throw new UserNotFoundException("User with ID " + userId + " not found");
        }
        
        return profile;
    }
    
    /**
     * Updates user profile information.
     * Allows modification of user details such as email, name, and preferences.
     * 
     * @param userId The ID of the user to update
     * @param profile The updated profile information
     * @return true if update successful, false otherwise
     */
    public boolean updateUserProfile(int userId, UserProfile profile) {
        try {
            db.updateUser(userId, profile);
            logger.info("User profile updated successfully for user: " + userId);
            return true;
        } catch (Exception e) {
            logger.error("Failed to update user profile: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * Deletes a user account from the system.
     * Permanently removes user data and associated records.
     * 
     * @param userId The ID of the user to delete
     * @param confirmPassword Password confirmation for security
     * @return true if deletion successful, false otherwise
     * @throws SecurityException if password confirmation fails
     */
    public boolean deleteUser(int userId, String confirmPassword) throws SecurityException {
        User user = db.findUserById(userId);
        
        if (!verifyPassword(user, confirmPassword)) {
            throw new SecurityException("Password confirmation failed");
        }
        
        return db.deleteUser(userId);
    }
    
    /**
     * Resets user password using email verification.
     * Sends a password reset link to the user's email.
     * 
     * @param email The email address of the user
     * @return true if reset email sent successfully
     */
    public boolean resetPassword(String email) {
        User user = db.findUserByEmail(email);
        
        if (user != null) {
            String resetToken = generateResetToken();
            sendResetEmail(user.getEmail(), resetToken);
            return true;
        }
        
        return false;
    }
    
    /**
     * Changes user password.
     * Requires current password verification before allowing change.
     * 
     * @param userId The ID of the user
     * @param currentPassword The current password
     * @param newPassword The new password to set
     * @return true if password changed successfully
     * @throws SecurityException if current password is incorrect
     */
    public boolean changePassword(int userId, String currentPassword, String newPassword) throws SecurityException {
        User user = db.findUserById(userId);
        
        if (!verifyPassword(user, currentPassword)) {
            throw new SecurityException("Current password is incorrect");
        }
        
        validatePassword(newPassword);
        String hashedPassword = hashPassword(newPassword);
        return db.updatePassword(userId, hashedPassword);
    }
    
    /**
     * Searches for users by username pattern.
     * Returns a list of users matching the search criteria.
     * 
     * @param searchPattern The pattern to search for
     * @param limit Maximum number of results to return
     * @return List of matching users
     */
    public static List<User> searchUsers(String searchPattern, int limit) {
        return DatabaseConnection.searchUsers(searchPattern, limit);
    }
    
    // Private helper methods without JavaDoc
    private String hashPassword(String password) {
        return PasswordHasher.hash(password);
    }
    
    private boolean verifyPassword(User user, String password) {
        return PasswordHasher.verify(password, user.getPasswordHash());
    }
    
    private void validateEmail(String email) throws ValidationException {
        if (!email.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
            throw new ValidationException("Invalid email format");
        }
    }
    
    private void validatePassword(String password) throws ValidationException {
        if (password.length() < 8) {
            throw new ValidationException("Password must be at least 8 characters");
        }
    }
    
    protected String generateResetToken() {
        return TokenGenerator.generate();
    }
    
    protected void sendResetEmail(String email, String token) {
        EmailService.send(email, "Password Reset", "Reset token: " + token);
    }
}

// Made with Bob
