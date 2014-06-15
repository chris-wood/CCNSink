require "openssl"
puts OpenSSL::BN::generate_prime(ARGV[0].to_i)
